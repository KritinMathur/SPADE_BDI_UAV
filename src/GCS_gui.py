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
        b = self.MyBehav()
        self.add_behaviour(b)

    def get_mav_parties(self):
        return self.mav_parties

    def set_add_mav(self):
        print('Add MAV Command at spade')
        #self.mav_parties[] = gcs_ui

    def set_remove_mav(self):
        pass



class AuctionLog(QtWidgets.QDialog,Ui_Auction_log_Dialog):
    def __init__(self):
        super(AuctionLog,self).__init__()
        self.setupUi(self)

class AddMAV(QtWidgets.QDialog,Ui_Add_mav_Dialog):
    def __init__(self):
        super(AddMAV,self).__init__()
        self.setupUi(self)
        self.current_JIT_ID = None
        self.current_MAV_NAME =None

        self.Add_mav_buttonBox.accepted.connect(self.add_mav_accept)
        self.Add_mav_buttonBox.rejected.connect(self.add_mav_reject)

    def add_mav_accept(self):
        
        print('trigger accept')
        if self.mavname_lineEdit.text() != '' and self.jit_id_lineEdit.text() != '' :

            # + check if already exist

            mav_info_dict = {'Name': self.mavname_lineEdit.text() , 'JIT ID':self.jit_id_lineEdit.text() }
            gcs.mav_parties.append(mav_info_dict['JIT ID'])
            gcs_ui.mav_parties_list.append(mav_info_dict)
            gcs_ui.update_gcs_agent()
            
            self.accept()

        self.reject()

    def edit_mav_accept(self):
        print('trigger accept')
        
        if self.mavname_lineEdit.text() != '' and self.jit_id_lineEdit.text() != '' :
            for i,mav_party in  enumerate(gcs.mav_parties):
                if mav_party == self.current_JIT_ID:
                    gcs.mav_parties[i] = self.jit_id_lineEdit.text()
                    break

            for i,mav_party in enumerate(gcs_ui.mav_parties_list):
                if mav_party['Name'] == self.current_MAV_NAME and mav_party['JIT ID'] == self.current_JIT_ID:
                    gcs_ui.mav_parties_list[i]['Name'] = self.mavname_lineEdit.text()
                    gcs_ui.mav_parties_list[i]['JIT ID'] = self.jit_id_lineEdit.text()
                    break

            gcs_ui.update_gcs_agent()


            if gcs_ui.edit_mav_pushButton.isEnabled():
                gcs_ui.edit_mav_pushButton.setEnabled(False)

            if gcs_ui.remove_mav_pushButton.isEnabled():   
                gcs_ui.remove_mav_pushButton.setEnabled(False)

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
    
    def setup_gcs_agent(self):
        mav_parties =  gcs.get_mav_parties()
        
        self.mav_parties_list = [{'Name':mav_party,'JIT ID':mav_party} for mav_party in mav_parties]   

        self.connected_mav_list.clear()
        for mav_party in self.mav_parties_list:
            self.connected_mav_list.addItem(QtWidgets.QListWidgetItem(mav_party['Name']))
    
    def update_gcs_agent(self):

        self.connected_mav_list.clear()
        for mav_party in self.mav_parties_list:
            self.connected_mav_list.addItem(QtWidgets.QListWidgetItem(mav_party['Name']))

    def handleAddMAV(self):

        self.add_mav_dialog = AddMAV()
        self.add_mav_dialog.show()
    
    def handleEditMAV(self):
        
        mav_name  = self.connected_mav_list.currentItem().text()
        print(mav_name)

        for mav_party in self.mav_parties_list:
            print(mav_party['Name'],mav_party['JIT ID'])
            print(mav_party['Name'] == mav_name)
            if mav_party['Name'] == mav_name:
                mav_jit = mav_party['JIT ID']
                break

        self.add_mav_dialog = AddMAV()
        self.add_mav_dialog.jit_id_lineEdit.setText(mav_jit)
        self.add_mav_dialog.mavname_lineEdit.setText(mav_name)
        self.add_mav_dialog.current_JIT_ID = mav_jit
        self.add_mav_dialog.current_MAV_NAME = mav_name
        self.add_mav_dialog.Add_mav_buttonBox.accepted.disconnect()
        self.add_mav_dialog.Add_mav_buttonBox.accepted.connect(self.add_mav_dialog.edit_mav_accept)
        self.add_mav_dialog.show()

    def handleConnectRowChange(self):

        if not self.edit_mav_pushButton.isEnabled():
            self.edit_mav_pushButton.setEnabled(True)

        if not self.remove_mav_pushButton.isEnabled():   
            self.remove_mav_pushButton.setEnabled(True)
     

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