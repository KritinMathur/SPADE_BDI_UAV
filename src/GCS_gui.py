import os
import time
import random
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

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWebEngineWidgets import QWebEngineView
from gui.GCS import Ui_MainWindow
from gui.AuctionLog import Ui_Auction_log_Dialog
from gui.AddEdit_MAV import Ui_Add_mav_Dialog        

import geospatial

class GCSAgent(PubSubMixin,Agent):

    class TelemSubscriber(CyclicBehaviour):

        async def on_start(self):
            await gcs.pubsub.purge('pubsub.localhost', "Telemetry_node")

        async def run(self):

            telem_payload = await gcs.pubsub.get_items('pubsub.localhost', "Telemetry_node")
            
            #telem_literal = telem_payload[-1].data
            #telem = json.loads(telem_literal)

            telem_literal_lst = [ json.loads(telem.data) for telem in telem_payload ]

            #update telemetry log
            await gcs.update_mav_logs(telem_literal_lst)

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

            if gcs_ui.active_auction:
                gcs_ui.active_auction = False

                alloc_mav_lst,alloc_auction_data = auction()

                for mav_name,auction_data in zip(alloc_mav_lst,alloc_auction_data):
                    send_payload = {'ID' : mav_name,'cmd':'set_role_mission', 'data': auction_data }
                    print(send_payload)
                    await gcs.pubsub.publish('pubsub.localhost', "Cmd_node", json.dumps(send_payload), item_id = mav_name)

            if gcs_ui.active_do_mission:
                gcs_ui.active_do_mission = False

                send_payload = {'ID' : gcs_ui.action_mav_name,'cmd':'do_mission', 'data': None }
                print(send_payload)
                await gcs.pubsub.publish('pubsub.localhost', "Cmd_node", json.dumps(send_payload), item_id = gcs_ui.action_mav_name)

            if gcs_ui.active_pause_mission:
                gcs_ui.active_pause_mission = False

                send_payload = {'ID' : gcs_ui.action_mav_name,'cmd':'pause_mission', 'data': None }
                print(send_payload)
                await gcs.pubsub.publish('pubsub.localhost', "Cmd_node", json.dumps(send_payload), item_id = gcs_ui.action_mav_name)

            if gcs_ui.active_land:
                gcs_ui.active_land = False

                send_payload = {'ID' : gcs_ui.action_mav_name,'cmd':'do_land', 'data': None }
                print(send_payload)
                await gcs.pubsub.publish('pubsub.localhost', "Cmd_node", json.dumps(send_payload), item_id = gcs_ui.action_mav_name) 

            if gcs_ui.active_RTL:
                gcs_ui.active_RTL = False

                send_payload = {'ID' : gcs_ui.action_mav_name,'cmd':'do_rtl', 'data': None }
                print(send_payload)
                await gcs.pubsub.publish('pubsub.localhost', "Cmd_node", json.dumps(send_payload), item_id = gcs_ui.action_mav_name)              


            await asyncio.sleep(1)



    # class MyBehav(CyclicBehaviour):

    #     class FIPA_Task_auction:
    #         class Handel_Online(CyclicBehaviour):
    #             async def run(self):
    #                 msg = await self.receive()
    #                 if msg is not None:
    #                     mav_party = msg.body
    #                     print(f'IN - Online from {mav_party} to {args.name}')
                        
    #                     print(f'OUT - Task Cost from {args.name} to {mav_party}')
    #                     msg = Message(to=f"{mav_party}@{args.server}")
    #                     msg.set_metadata("performative", "task_cost")
    #                     msg.body = gcs.task_cost # TASK Cost calculation
    #                     await self.send(msg)

    #                 await asyncio.sleep(1)

    #         class Handel_Bids(CyclicBehaviour):
    #             async def run(self):
    #                 msg = await self.receive()
    #                 if msg is not None:

    #                     msg_data = json.loads(msg.body)
    #                     mav_party = msg_data['name']
    #                     mav_bid = msg_data['data']
    #                     print(f'IN - Bids from {mav_party} to {args.name}')

    #                     if mav_bid < gcs.auction_threshold:
    #                         #REJECT BID
    #                         print(f'OUT - Reject Bid from {args.name} to {mav_party}')
    #                         msg = Message(to=f"{mav_party}@{args.server}")
    #                         msg.set_metadata("performative", "reject_bid")
    #                         msg.body = args.name
    #                         await self.send(msg)

    #                     else:
    #                         #ACCEPT BID
    #                         print(f'OUT - Accept Bid from {args.name} to {mav_party}')
    #                         msg = Message(to=f"{mav_party}@{args.server}")
    #                         msg.set_metadata("performative", "accept_bid")
    #                         msg.body = args.name
    #                         await self.send(msg)

    #                         gcs.current_bids[mav_party] = mav_bid 

    #                 await asyncio.sleep(1)
        
    #     async def on_start(self):
    #         print("Starting behaviour . . .")
    #         self.counter = 0

    #     async def run(self):
    #         print("Counter: {}".format(self.counter))
    #         self.counter += 1
            
    #         mav_ID = await aioconsole.ainput('Enter ID :-  ')
    #         mav_command = await aioconsole.ainput('Enter Command :-  ')
    #         send_payload = {'ID' : mav_ID, 'data':mav_command}

    #         await gcs.pubsub.publish('pubsub.localhost', "Cmd_node", json.dumps(send_payload))
    #         time.sleep(4)

    #         if send_payload['data'] == 'get_info':
    #             Telem_payload = await gcs.pubsub.get_items('pubsub.localhost', "Telemetry_node")
    #             telem_literal = Telem_payload[-1].data
    #             telem = json.loads(telem_literal)
    #             print('Response ID :'+ telem['ID'])
    #             print(telem['data'])

    #         #START AUCTION
    #         if send_payload['ID'] == 'start_auction':
                
    #             gcs.auction_file_path = send_payload['data']
    #             gcs.auction_threshold = 1
    #             gcs.task_cost = '4'

    #             #start auction
    #             for mav_party in gcs.mav_parties:        

    #                 print(f'OUT - Start Auction from {args.name} to {mav_party}')
    #                 msg = Message(to=f"{mav_party}@{args.server}")
    #                 msg.set_metadata("performative", "start_auction")
    #                 msg.body = args.name
    #                 await self.send(msg)

    #             while True:
    #                 gcs.current_bids = {}
    #                 deadline = 7
    #                 await asyncio.sleep(deadline)

    #                 '''
    #                 temp = min(gcs.current_bids.values())
    #                 res = [key for key in gcs.current_bids if gcs.current_bids[key] == temp]
    #                 print('min bid - ', res)
    #                 '''

    #                 if len(gcs.current_bids) > 1:
    #                     # threshold +
    #                     gcs.auction_threshold += 1

    #                     for mav_party in gcs.current_bids:
    #                         print(f'OUT - Threshold Plus from {args.name} to {mav_party}')
    #                         msg = Message(to=f"{mav_party}@{args.server}")
    #                         msg.set_metadata("performative", "threshold_plus")
    #                         msg.body = gcs.task_cost
    #                         await self.send(msg)

    #                 else :
    #                     break

    #             if len(gcs.current_bids) == 1: 
    #                 # allocate task
    #                 mav_party,bid_value = gcs.current_bids.popitem()
    #                 print(bid_value)

    #                 print(f'OUT - Allocate Task from {args.name} to {mav_party}')
    #                 msg = Message(to=f"{mav_party}@{args.server}")
    #                 msg.set_metadata("performative", "allocate_task")
    #                 msg.body = args.name
    #                 await self.send(msg)

    #             else:
    #                 print(len(gcs.current_bids))
    #                 raise Exception

    
    #         await asyncio.sleep(1)

    async def setup(self):

        t = time.localtime()
        current_time = time.strftime("[START %H:%M:%S ]\n", t)
        
        self.mav_parties = ['test','test2','test3','test4','test5']
        self.mav_missions = []
        self.mav_logs = {}
        self.logs_data = [current_time]

        # CNP_online_template  = Template()
        # CNP_online_template.set_metadata("performative","online")
        # CNP_bids_template = Template()
        # CNP_bids_template.set_metadata("performative","bids")

        # CNP_online_behave = self.MyBehav.FIPA_Task_auction.Handel_Online()
        # CNP_bids_behave = self.MyBehav.FIPA_Task_auction.Handel_Bids()

        # self.add_behaviour(CNP_online_behave,CNP_online_template)
        # self.add_behaviour(CNP_bids_behave,CNP_bids_template)

        print("GCS Agent starting . . .")
        telem_subscriber_behaviour = self.TelemSubscriber()
        self.add_behaviour(telem_subscriber_behaviour)
        cmd_publisher_behaviour = self.CmdPublisher()
        self.add_behaviour(cmd_publisher_behaviour)

    async def update_mav_logs(self,telem_literal_lst):
        #print(telem_literal_lst)
        gcs.current_telem_log = telem_literal_lst

        #Add new mav to mav logs
        for telem in gcs.current_telem_log:
            if telem['ID'] not in self.mav_logs.keys():
                self.mav_logs[telem['ID']] = []

        #Update mav logs
        for telem in gcs.current_telem_log:
            self.mav_logs[telem['ID']].append(telem['data'])

            if len(self.mav_logs[telem['ID']]) >= 25:
                self.mav_logs[telem['ID']].pop(0)

def auction():

    if gcs_ui.alloc_mav_name =='[All]' and gcs_ui.alloc_role == '[Auto]' and gcs_ui.alloc_mission_name =='[Auto]' and gcs_ui.alloc_parent_mav == '[Auto]':
        
        M_name = []
        CM = []
        for mission_data in gcs.mav_missions:
            clat,clon = 0,0
            for mission_waypoint in mission_data['data']:
                clat += float(mission_waypoint[8])
                clon += float(mission_waypoint[9])

            clat /= len(mission_data['data'])
            clon /= len(mission_data['data'])

            CM.append((clat,clon))
            M_name.append(mission_data['name'])

        D = [[0 for _ in CM] for _ in CM] 
        for i,centroid_i in enumerate(CM):
            for j,centroid_j in enumerate(CM):
                D[i][j] = geospatial.distance(*centroid_i,*centroid_j)

        zip_cm_name = zip(D,M_name)
        zip_sorted = sorted(zip_cm_name,key=lambda x: sum(x[0]))
        M_name,D = [ele for _,ele in zip_sorted],[ele for ele,_ in zip_sorted]

        num_coordinater = round((len(M_name)-1)/3)

        alloc_auction_data = []

        for i,mission in enumerate(M_name):
            
            alloc_mission_data = next(mission_data for mission_data in gcs.mav_missions if mission_data["name"] == mission)

            if i == 0:
                alloc_auction_data.append({'role':'Master','parent':'[None]','mission':alloc_mission_data})
            elif i <= num_coordinater:
                alloc_auction_data.append({'role':'Coordinator','parent':'[None]','mission':alloc_mission_data})
            else:
                alloc_auction_data.append({'role':'Agent','parent':'[None]','mission':alloc_mission_data})

        #Task Cost
        for mission_data in alloc_mission_data:

            alloc_mission_data = mission_data['mission']

            total_distance = 0
            for i,mission_waypoint in enumerate(alloc_mission_data['data']):

                if i+2== len(alloc_mission_data['data']):
                    break
                elif i == 0:
                    prev_waypoint = (mission_waypoint[8],mission_waypoint[9])
                else:
                    current_waypoint = (mission_waypoint[8],mission_waypoint[9])
                    total_distance += geospatial.distance(*prev_waypoint,*current_waypoint)
                    prev_waypoint = current_waypoint
                
            mission_data['score'] 


    else:
        alloc_mav_lst = [gcs_ui.alloc_mav_name]
        alloc_mission_data = next(mission_data for mission_data in gcs.mav_missions if mission_data["name"] == gcs_ui.alloc_mission_name)
        
        alloc_auction_data = [{'role' : gcs_ui.alloc_role,'parent' : gcs_ui.alloc_parent_mav,'mission':alloc_mission_data}]

    return (alloc_mav_lst,alloc_auction_data)
    #print(self.alloc_auction_data)


class TelemetryThread(QtCore.QThread):
    change_telem_value = QtCore.pyqtSignal(object)

    def run(self):
        while True:
            current_telem_log = gcs.current_telem_log
            time.sleep(1)
            self.change_telem_value.emit(current_telem_log)



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

class MplCanvas(FigureCanvas):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        self.axes.get_xaxis().set_visible(False)
        super(MplCanvas, self).__init__(fig)

class Gcs(QtWidgets.QMainWindow,Ui_MainWindow):
    def __init__(self):
        super(Gcs, self).__init__()

        #Icon
        self.setWindowIcon(QtGui.QIcon('src/gui/logo.png'))

        #Create GUI
        self.setupUi(self)

        #Create Connections and add 3rd party widgets
        self.connectUi()

        #Setup
        self.setup_gcs_agent()

    def connectUi(self):

        #MAV
        self.add_mav_pushButton.clicked.connect(self.handleAddMAV)
        self.edit_mav_pushButton.clicked.connect(self.handleEditMAV)
        self.connected_mav_list.currentRowChanged.connect(self.handleConnectRowChange)

        #Auction
        self.start_auction_pushButton.clicked.connect(self.handleStartAuction)

        #Mission
        self.do_mission_pushButton.clicked.connect(self.handleDoMission)
        self.pause_missions_pushButton.clicked.connect(self.handlePauseMission)
        self.land_pushButton.clicked.connect(self.handleLand)
        self.rtl_pushButton.clicked.connect(self.handleRTL)

        #SIM
        self.start_sim_pushButton.clicked.connect(self.handleStartSim)
        self.stop_sim_pushButton.clicked.connect(self.handleStopSim)
        self.set_fault_pushButton.clicked.connect(self.handleSetFault)

        #Menu Bar
        self.actionAdd_Plans.triggered.connect(self.filemenu_addplans)
        self.actionExport_Logs.triggered.connect(self.filemenu_exportlogs)
        self.actionPX.triggered.connect(self.editmenu_addsimpath_px)       

        #Maps
        self.missions_map_widget = QWebEngineView()
        self.loadMissionPage() 
        self.Missions_map_hlay.addWidget(self.missions_map_widget)

        #Plots
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.plots_telem_hlay.addWidget(self.canvas)
        self.mav_name_plots_listWidget.currentRowChanged.connect(self.handlePlotMavRowChange)

    
    def setup_gcs_agent(self):

        self.current_selected_mav = None
        self.current_plot_mav = None
        self.active_faults = False
        self.active_auction = False
        self.active_do_mission = False
        self.active_pause_mission = False
        self.active_land = False
        self.active_RTL = False

        self.px4_sim_path = None
        self.ardupilot_sim_path = None
        
        self.update_gcs_agent()
        self.start_telem_thread()

    def start_telem_thread(self):
        self.telem_thread = TelemetryThread()
        self.telem_thread.change_telem_value.connect(self.update_telem_value)
        self.telem_thread.start()

    def update_telem_value(self,current_telem_log):

        #print(self.current_selected_mav)
        print(current_telem_log)

        #MAV Tab
        if self.current_selected_mav:

            
            for telem in current_telem_log:
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

        #Mission Tab
        if self.AllTabWidget.currentIndex() == 3:
            #print(current_telem_log)
            js_safe_telemetry = json.dumps(current_telem_log)
            #print(js_safe_telemetry)
            self.missions_map_widget.page().runJavaScript("getTelemetryInfo({})".format(js_safe_telemetry))

        #Analyse Tab - logging  
        for telem in current_telem_log:
            logs_mav = telem['data']['log']
            for log in logs_mav:
                gcs.logs_data.append(log+'\n')
                self.logs_textBrowser.append(log)

        #Analyse Tab - Plots
        self.update_plot()

    
    def update_gcs_agent(self):

        self.connected_mav_list.clear()
        self.mav_name_simulate_faults_comboBox.clear()
        self.mav_name_comboBox.clear()
        self.parent_mav_comboBox.clear()
        self.mav_name_action_comboBox.clear()
        self.mav_name_plots_listWidget.clear()
        
        self.mav_name_simulate_faults_comboBox.addItem('[All]')
        self.mav_name_comboBox.addItem('[All]')
        self.parent_mav_comboBox.addItem('[Auto]')
        self.parent_mav_comboBox.addItem('[None]')
        self.mav_name_action_comboBox.addItem('[All]')

        for mav_party in gcs.mav_parties:
            self.connected_mav_list.addItem(QtWidgets.QListWidgetItem(mav_party))
            self.mav_name_simulate_faults_comboBox.addItem(mav_party)
            self.mav_name_comboBox.addItem(mav_party)
            self.parent_mav_comboBox.addItem(mav_party)
            self.mav_name_action_comboBox.addItem(mav_party)
            self.mav_name_plots_listWidget.addItem(QtWidgets.QListWidgetItem(mav_party))

        
        self.missions_listWidget.clear()
        self.MMU_comboBox.clear()

        self.MMU_comboBox.addItem('[Auto]')
        
        for mav_mission in gcs.mav_missions:
            self.missions_listWidget.addItem(QtWidgets.QListWidgetItem(mav_mission['name']))
            self.MMU_comboBox.addItem(mav_mission['name'])

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

    def handleStartAuction(self):
        
        self.alloc_mav_name = self.mav_name_comboBox.currentText()
        self.alloc_role = self.selected_role_comboBox.currentText()
        self.alloc_parent_mav = self.parent_mav_comboBox.currentText()  
        self.alloc_mission_name = self.MMU_comboBox.currentText()

        self.active_auction = True

    def handleDoMission(self):
        
        self.action_mav_name = self.mav_name_action_comboBox.currentText()
        self.active_do_mission = True

    def handlePauseMission(self):

        self.action_mav_name = self.mav_name_action_comboBox.currentText()
        self.active_pause_mission = True

    def handleLand(self):

        self.action_mav_name = self.mav_name_action_comboBox.currentText()
        self.active_land = True

    def handleRTL(self):

        self.action_mav_name = self.mav_name_action_comboBox.currentText()
        self.active_RTL = True

    def handlePlotMavRowChange(self):

        if self.mav_name_plots_listWidget.currentItem():
            self.current_plot_mav = self.mav_name_plots_listWidget.currentItem().text()

    def handleStartSim(self):
        if self.px4_sim_path:
            num_px4 = self.px4_sim_spinBox.value()
            os.system(f"gnome-terminal -e 'bash ./src/launch_px4_sim.sh 2.4713686 -76.5975746 {self.px4_sim_path} {num_px4}'")

            self.start_sim_pushButton.setEnabled(False)

        else:
            print('SIM PATH NOT SET')
            print(gcs.mav_parties)


    def handleStopSim(self):
        os.system('pkill -9 -f /Tools/gazebo_sitl_multiple_run.sh')
        self.start_sim_pushButton.setEnabled(True)


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

    def filemenu_addplans(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(self,"QFileDialog.getOpenFileNames()", "","All Files (*);;Python Files (*.py)", options=options)
        
        if files:
            print(files)

            for file_name in files:

                mission_data = {'name': file_name.split('/')[-1] ,'path':file_name, 'data': [] }

                with open(file_name) as f:
                    for i, line in enumerate(f):
                        if i==0:
                            if not line.startswith('QGC WPL 110'):
                                raise Exception('File is not supported WP version')
                        else:
                            linearray=line.split('\t')
                            mission_data['data'].append(linearray.copy())

                gcs.mav_missions.append(mission_data)

            self.update_gcs_agent()

    def filemenu_exportlogs(self):
        name = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File')
        print(name)

        if name != ('',''):
            file = open(name[0],'w')
            text = gcs.logs_data
            file.writelines(text)
            file.close()

    def editmenu_addsimpath_px(self):
        file = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))
        if file != '':
            self.px4_sim_path = file
            print(self.px4_sim_path)

    def loadMissionPage(self):

        with open('src/live_location.html', 'r') as f:

            html = f.read()
            print('Loaded HTML')
            self.missions_map_widget.setHtml(html)

    def update_plot(self):

        self.ydata = []
        self.xdata = []
        self.canvas.axes.cla()

        if self.mav_name_plots_listWidget.currentItem():
            if self.current_plot_mav:
                
                data = gcs.mav_logs[self.current_plot_mav]

                for telemetry_unit in data:
                    self.ydata.append(telemetry_unit['telem']['pos']['alt_abs'])
                    self.xdata.append(telemetry_unit['timestamp'])
            
                self.canvas.axes.plot(self.xdata, self.ydata, 'r')
                self.canvas.draw()
        

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