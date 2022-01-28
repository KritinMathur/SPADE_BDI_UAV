import time
import asyncio
import aioconsole
from spade.message import Message
from spade.template import Template
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade_pubsub import PubSubMixin
import json

import argparse
import agentspeak
from spade import quit_spade
from spade_bdi.bdi import BDIAgent
import asyncio

from PyQt5 import QtWidgets, QtCore
from gui.GCS import Ui_MainWindow
from gui.AuctionLog import Ui_Auction_log_Dialog
from gui.AddEdit_MAV import Ui_Add_mav_Dialog        

class GCSAgent(PubSubMixin,Agent):

    class TelemSubscriber(CyclicBehaviour):

        async def on_start(self):
            await gcs.pubsub.purge('pubsub.localhost', "Telemetry_node")

        async def run(self):

            telem_payload = await gcs.pubsub.get_items('pubsub.localhost', "Telemetry_node")
            
            #telem_literal = telem_payload[-1].data
            #telem = json.loads(telem_literal)

            telem_literal_lst = [ json.loads(telem.data) for telem in telem_payload ]

            #print(telem_literal_lst)
            gcs.telem_log = telem_literal_lst

            await asyncio.sleep(1)

    class CmdPublisher(CyclicBehaviour):

        async def on_start(self):
            await gcs.pubsub.purge('pubsub.localhost', "Cmd_node")
            await asyncio.sleep(1)

        async def run(self):

            if gcs_ui.active_faults:
                gcs_ui.active_faults = False

                send_payload = {'ID' : gcs_ui.faulty_mav_name,'cmd':'set_fault','data':gcs_ui.current_faults}
                print(send_payload)
                await gcs.pubsub.publish('pubsub.localhost', "Cmd_node", json.dumps(send_payload), item_id = gcs_ui.faulty_mav_name)

                await asyncio.sleep(1)



    class MyBehav(CyclicBehaviour):

        class FIPA_Task_auction:
            class Handel_Online(CyclicBehaviour):
                async def run(self):
                    msg = await self.receive()
                    if msg is not None:
                        mav_party = msg.body
                        print(f'IN - Online from {mav_party} to {args.name}')
                        
                        print(f'OUT - Task Cost from {args.name} to {mav_party}')
                        msg = Message(to=f"{mav_party}@{args.server}")
                        msg.set_metadata("performative", "task_cost")
                        msg.body = gcs.task_cost # TASK Cost calculation
                        await self.send(msg)

                    await asyncio.sleep(1)

            class Handel_Bids(CyclicBehaviour):
                async def run(self):
                    msg = await self.receive()
                    if msg is not None:

                        msg_data = json.loads(msg.body)
                        mav_party = msg_data['name']
                        mav_bid = msg_data['data']
                        print(f'IN - Bids from {mav_party} to {args.name}')

                        if mav_bid < gcs.auction_threshold:
                            #REJECT BID
                            print(f'OUT - Reject Bid from {args.name} to {mav_party}')
                            msg = Message(to=f"{mav_party}@{args.server}")
                            msg.set_metadata("performative", "reject_bid")
                            msg.body = args.name
                            await self.send(msg)

                        else:
                            #ACCEPT BID
                            print(f'OUT - Accept Bid from {args.name} to {mav_party}')
                            msg = Message(to=f"{mav_party}@{args.server}")
                            msg.set_metadata("performative", "accept_bid")
                            msg.body = args.name
                            await self.send(msg)

                            gcs.current_bids[mav_party] = mav_bid 

                    await asyncio.sleep(1)
        
        async def on_start(self):
            print("Starting behaviour . . .")
            self.counter = 0

        async def run(self):
            print("Counter: {}".format(self.counter))
            self.counter += 1
            
            mav_ID = await aioconsole.ainput('Enter ID :-  ')
            mav_command = await aioconsole.ainput('Enter Command :-  ')
            send_payload = {'ID' : mav_ID, 'data':mav_command}

            await gcs.pubsub.publish('pubsub.localhost', "Cmd_node", json.dumps(send_payload))
            time.sleep(4)

            if send_payload['data'] == 'get_info':
                Telem_payload = await gcs.pubsub.get_items('pubsub.localhost', "Telemetry_node")
                telem_literal = Telem_payload[-1].data
                telem = json.loads(telem_literal)
                print('Response ID :'+ telem['ID'])
                print(telem['data'])

            #START AUCTION
            if send_payload['ID'] == 'start_auction':
                
                gcs.auction_file_path = send_payload['data']
                gcs.auction_threshold = 1
                gcs.task_cost = '4'

                #start auction
                for mav_party in gcs.mav_parties:        

                    print(f'OUT - Start Auction from {args.name} to {mav_party}')
                    msg = Message(to=f"{mav_party}@{args.server}")
                    msg.set_metadata("performative", "start_auction")
                    msg.body = args.name
                    await self.send(msg)

                while True:
                    gcs.current_bids = {}
                    deadline = 7
                    await asyncio.sleep(deadline)

                    '''
                    temp = min(gcs.current_bids.values())
                    res = [key for key in gcs.current_bids if gcs.current_bids[key] == temp]
                    print('min bid - ', res)
                    '''

                    if len(gcs.current_bids) > 1:
                        # threshold +
                        gcs.auction_threshold += 1

                        for mav_party in gcs.current_bids:
                            print(f'OUT - Threshold Plus from {args.name} to {mav_party}')
                            msg = Message(to=f"{mav_party}@{args.server}")
                            msg.set_metadata("performative", "threshold_plus")
                            msg.body = gcs.task_cost
                            await self.send(msg)

                    else :
                        break

                if len(gcs.current_bids) == 1: 
                    # allocate task
                    mav_party,bid_value = gcs.current_bids.popitem()
                    print(bid_value)

                    print(f'OUT - Allocate Task from {args.name} to {mav_party}')
                    msg = Message(to=f"{mav_party}@{args.server}")
                    msg.set_metadata("performative", "allocate_task")
                    msg.body = args.name
                    await self.send(msg)

                else:
                    print(len(gcs.current_bids))
                    raise Exception

    
            await asyncio.sleep(1)

    async def setup(self):

        self.mav_parties = ['test','test2','test3','test4','test5']

        CNP_online_template  = Template()
        CNP_online_template.set_metadata("performative","online")
        CNP_bids_template = Template()
        CNP_bids_template.set_metadata("performative","bids")

        CNP_online_behave = self.MyBehav.FIPA_Task_auction.Handel_Online()
        CNP_bids_behave = self.MyBehav.FIPA_Task_auction.Handel_Bids()

        self.add_behaviour(CNP_online_behave,CNP_online_template)
        self.add_behaviour(CNP_bids_behave,CNP_bids_template)

        print("GCS Agent starting . . .")
        telem_subscriber_behaviour = self.TelemSubscriber()
        self.add_behaviour(telem_subscriber_behaviour)
        cmd_publisher_behaviour = self.CmdPublisher()
        self.add_behaviour(cmd_publisher_behaviour)

class TelemetryThread(QtCore.QThread):
    change_telem_value = QtCore.pyqtSignal(object)

    def run(self):
        while True:
            telem_log = gcs.telem_log
            time.sleep(1)
            self.change_telem_value.emit(telem_log)



class AuctionLog(QtWidgets.QDialog,Ui_Auction_log_Dialog):
    def __init__(self):
        super(AuctionLog,self).__init__()
        self.setupUi(self)

class AddMAV(QtWidgets.QDialog,Ui_Add_mav_Dialog):
    def __init__(self):
        super(AddMAV,self).__init__()
        self.setupUi(self)
        self.current_MAV = None

        self.Add_mav_buttonBox.accepted.connect(self.add_mav_accept)
        self.Add_mav_buttonBox.rejected.connect(self.add_mav_reject)

    def add_mav_accept(self):
        
        print('trigger accept')
        if self.jit_id_lineEdit.text() != '' :

            # + check if already exist

            mav_info = self.jit_id_lineEdit.text()
            gcs.mav_parties.append(mav_info)
            gcs_ui.update_gcs_agent()
            
            self.accept()

        self.reject()

    def edit_mav_accept(self):
        print('trigger accept')
        
        if self.jit_id_lineEdit.text() != '' :
            for i,mav_party in  enumerate(gcs.mav_parties):
                if mav_party == self.current_MAV:
                    gcs.mav_parties[i] = self.jit_id_lineEdit.text()
                    break

            gcs_ui.update_gcs_agent()


            if gcs_ui.edit_mav_pushButton.isEnabled():
                gcs_ui.edit_mav_pushButton.setEnabled(False)

            if gcs_ui.remove_mav_pushButton.isEnabled():   
                gcs_ui.remove_mav_pushButton.setEnabled(False)

            gcs_ui.current_selected_mav = None

            self.accept()

        self.reject()

        
    def add_mav_reject(self):
        print('trigger reject')
        self.reject()

class Gcs(QtWidgets.QMainWindow,Ui_MainWindow):
    def __init__(self):
        super(Gcs, self).__init__()
        self.setupUi(self)

        self.setup_gcs_agent()

        self.add_mav_pushButton.clicked.connect(self.handleAddMAV)
        self.edit_mav_pushButton.clicked.connect(self.handleEditMAV)
        self.connected_mav_list.currentRowChanged.connect(self.handleConnectRowChange)
        self.set_fault_pushButton.clicked.connect(self.handleSetFault)
    
    def setup_gcs_agent(self):

        self.current_selected_mav = None
        self.active_faults = False
        
        self.connected_mav_list.clear()
        for mav_party in gcs.mav_parties:
            self.connected_mav_list.addItem(QtWidgets.QListWidgetItem(mav_party))
            self.mav_name_simulate_faults_comboBox.addItem(mav_party)

        self.start_telem_thread()

    def start_telem_thread(self):
        self.telem_thread = TelemetryThread()
        self.telem_thread.change_telem_value.connect(self.update_telem_value)
        self.telem_thread.start()

    def update_telem_value(self,telem_log):

        print(self.current_selected_mav)
        if self.current_selected_mav:

            
            for telem in telem_log:
                if telem['ID'] == self.current_selected_mav:
                    self.telem_current_mav = telem
                    break

            try:
                self.flight_status_textBrowser.setText('in air' if self.telem_current_mav['data']['telem']['state'] else 'landed')
                self.remaining_perc_lcdNumber.display(self.telem_current_mav['data']['telem']['batt'])
                self.latitude_lcdNumber.display(self.telem_current_mav['data']['telem']['pos']['lat'])
                self.longitude_lcdNumber.display(self.telem_current_mav['data']['telem']['pos']['lon'])
                self.altitude_abs_lcdNumber.display(self.telem_current_mav['data']['telem']['pos']['alt_abs'])
                self.altitude_rel_lcdNumber.display(self.telem_current_mav['data']['telem']['pos']['alt_rel'])
            except:
                print('Telemetry update error')
    
    def update_gcs_agent(self):

        self.connected_mav_list.clear()
        for mav_party in gcs.mav_parties:
            self.connected_mav_list.addItem(QtWidgets.QListWidgetItem(mav_party))
            self.mav_name_simulate_faults_comboBox.addItem(mav_party)

    def handleAddMAV(self):

        self.add_mav_dialog = AddMAV()
        self.add_mav_dialog.show()
    
    def handleEditMAV(self):
        
        mav_jit  = self.connected_mav_list.currentItem().text()
        print(mav_jit)

        self.add_mav_dialog = AddMAV()
        self.add_mav_dialog.jit_id_lineEdit.setText(mav_jit)
        self.add_mav_dialog.current_MAV = mav_jit
        self.add_mav_dialog.Add_mav_buttonBox.accepted.disconnect()
        self.add_mav_dialog.Add_mav_buttonBox.accepted.connect(self.add_mav_dialog.edit_mav_accept)
        self.add_mav_dialog.show()

    def handleConnectRowChange(self):

        if not self.edit_mav_pushButton.isEnabled():
            self.edit_mav_pushButton.setEnabled(True)

        if not self.remove_mav_pushButton.isEnabled():   
            self.remove_mav_pushButton.setEnabled(True)

        if self.connected_mav_list.currentItem():
            self.current_selected_mav = self.connected_mav_list.currentItem().text()

    def handleSetFault(self):
        self.faulty_mav_name = self.mav_name_simulate_faults_comboBox.currentText()

        low_battery = self.low_battery_checkBox.isChecked()
        gps_lost = self.gps_lost_checkBox.isChecked()
        rc_linkloss = self.rc_linkloss_checkBox.isChecked()
        data_linkloss = self.data_linkloss_checkBox.isChecked()
        sensor_failure = self.sensor_failure_checkBox.isChecked()
        no_neighbour = self.no_neighbour_checkBox.isChecked()
        near_neighbour = self.near_neighbour_checkBox.isChecked()

        self.current_faults = {'low_battery':low_battery,'gps_lost':gps_lost,'rc_linkloss':rc_linkloss,'data_linkloss':data_linkloss,'sensor_failure':sensor_failure,'no_neighbour':no_neighbour,'near_neighbour':near_neighbour}
        self.active_faults = True


        

if __name__ == "__main__":


    global args
    parser = argparse.ArgumentParser(description='GCS')
    parser.add_argument('--server', type=str,
                        default="localhost", help='XMPP server address.')
    parser.add_argument('--name', type=str, default="gcs",
                        help='XMPP name for the GCS.')
    parser.add_argument('--password', type=str,
                        default="password", help='XMPP password for the GCS.')
    args = parser.parse_args()

    gcs = GCSAgent("{}@{}".format(args.name, args.server),args.password)
    future = gcs.start()
    future.result()

    import sys
    app = QtWidgets.QApplication(sys.argv)
    gcs_ui = Gcs()
    gcs_ui.show()

    #print("Wait until user interrupts with ctrl+C")
    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        print("Stopping...")
    gcs.stop()