#Developed by Magnus Berg, 2024 for the University of Toronto, Mississauga Digital Scholarship Unit#

import os
import subprocess
from pathlib import Path
import sys
import FreeSimpleGUI as sg
import bagit

sg.theme('Reddit')

layout = [[sg.Text('AV Post-Digitization Packaging Application', font=("bold", 20))],
	[sg.Text('Select the video file created by Media Express', size=(40, 1)), sg.Input(key='-video-'), sg.FileBrowse()],
	[sg.Text('What is the filename for the tape? (DO NOT add file extension)', size=(40, 1)), sg.InputText(key='-filename-')],
	[sg.Text('Please select an output directory', size=(40, 1)), sg.Input(key='-dir-'), sg.FolderBrowse()],
	[sg.Submit(), sg.Cancel(), sg.Button('Reset', key='-reset-')],
	[sg.Multiline(size=(100, 5), key='-multiline-', autoscroll=True, visible=True, expand_y=True)],
	[sg.ProgressBar(100, orientation='h', expand_x=True, size=(3, 20), key='-PBAR-', visible=False)]]

window = sg.Window('AV Post-Digitization Packaging Application', layout, resizable=True).Finalize()
progress_bar = window.find_element('-PBAR-')
reset = window.find_element('-reset-')

def input_check(video_stream, user_filename, main_dir):
	if video_stream and user_filename and main_dir:
		process0 = True
	elif bool(video_stream) == False:
		process0 = False
	elif bool(user_filename) == False:
		process0 = False
	elif bool(main_dir) == False:
		process0=False

	return process0

def mas_dir_check(main_dir, master_dir):
#Makes the master directory
	try:
		master_dir_prep = os.mkdir(master_dir)
	except:
		process2 = False
	else:
		process2 = True
	
	return process2

def acc_dir_check(main_dir, access_dir):
#Makes the access directory
	try:
		access_dir_prep = os.mkdir(access_dir)
	except:
		process3 = False
	else:
		process3 = True

	return process3

def create_master(master_dir, master_file_name, user_filename, master_log, video_stream):
#creates a master file (ffv1 mkv) and md5 checksum file based on the video input
	master_md5 = os.path.join(master_dir, user_filename+'.md5')
	master_file_str = r'ffmpeg -i ' + str(video_stream) + ' -dn -c:v ffv1 -level 3 -g 1 -slicecrc 1 -slices 9 -copyts -c:a copy -loglevel error ' + str(master_file_name) + ' -f framemd5 -an ' + str(master_md5) 

	master_file = subprocess.run(master_file_str, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
	master_file.stdout = open(master_log, 'w')
	return master_file.returncode

def create_access(access_dir, access_file_name, video_stream, access_log):
#creates an access file (mp4) based on the video input
	access_file_str = r'ffmpeg -i ' + str(video_stream) + ' -c:v libx264 -copyts -filter:v "format=yuv422p" -crf 28 -movflags +faststart -loglevel error ' + str(access_file_name)	

	access_file = subprocess.run(access_file_str, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
	access_file.stdout = open(access_log, 'w')
	return access_file.returncode

def bag_files(main_dir):
#bags all files based on the Library of Congress's Bagit standard (including assigning checksums)
	bagstr = str(main_dir)
			
	try:
		bagit.make_bag(bagstr, {'Contact-Name': 'AV Post-Digitization Conversion Applet'})
	except:
		failure=True
	else:
		failure=False
	return failure


def the_gui():
	while True:
		event, values = window.read()
		if event == 'Submit':
			video_stream = values['-video-']
			user_filename = values['-filename-']
			main_dir = values['-dir-']
			
			status1 = input_check(video_stream, user_filename, main_dir)
			if status1 == False:
				window['-multiline-'].update('Please fill out all fields and try again.'+'/n', append=True)
				status = False
			else: 
				window['-multiline-'].update('Input accepted. Please wait.'+'\n', append=True)
				access_dir = os.path.join(main_dir, 'Access')
				master_dir = os.path.join(main_dir, 'Master')
				status2 = mas_dir_check(main_dir, master_dir)
		
				if status2==False:
					window['-multiline-'].update('Unable to continue conversion process. Ensure that no duplicate directories exist and try again.'+'\n', append=True)
					status3=False
			
				else:
					window['-multiline-'].update('Created Master directory'+'\n', append=True)
					status3 = acc_dir_check(main_dir, access_dir)
					if status3 == False:
						window['-multiline-'].update('Unable to continue conversion process. Ensure that no duplicate directories exist and try again.'+'\n', append=True)
						status4=False
					else:
						window['-multiline-'].update('Created Access directory'+'\n', append=True)
						status4=True


			if status4:
				access_file_name = os.path.join(access_dir, user_filename+'.mp4')
				master_file_name = os.path.join(master_dir, user_filename+'.mkv')
				master_log = os.path.join(master_dir, "ffreport.log")
				access_log = os.path.join(access_dir, "ffreport.log")

				window['-multiline-'].update('Attempting master file creation. Please wait.'+'\n', append=True)	
				progress_bar.update(visible=True)
				progress_bar.UpdateBar(0, 3)
				window.perform_long_operation(lambda: create_master(master_dir, master_file_name, user_filename, master_log, video_stream), '-Master Complete-')

		elif event == '-Master Complete-':
			status5={values[event]}
			if status5=={0}:
				if os.path.getsize(master_log) == 0:
					os.remove(master_log)
					window['-multiline-'].update('Derived new master file.'+'\n', append=True)
					window['-multiline-'].update('Attempting access file creation. Please wait.'+'\n', append=True)
					progress_bar.UpdateBar(1, 3)
					window.perform_long_operation(lambda: create_access(access_dir, access_file_name, video_stream, access_log), '-Access Complete-')
				else:
					window['-multiline-'].update('Master file creation failed. Please see log file.'+'\n', append=True)	
					window.write_event_value('-failure-', True)
			else:
				window.write_event_value('-failure-', True)

		elif event == '-Access Complete-':
			status6={values[event]}
			if status6=={0}:
				if os.path.getsize(access_log) == 0:
					os.remove(access_log)
					window['-multiline-'].update('Derived new access file.'+'\n', append=True)
					progress_bar.UpdateBar(2,3)
					status7=bag_files(main_dir)
					if status7:
						window.write_event_value('-failure-', True)
					elif status7==False:
						window.write_event_value('-failure-', False)
				else:
					window['-multiline-'].update('Access file creation failed. Please see log file.'+'\n', append=True)	
					window.write_event_value('-failure-', True)

			else:
				window.write_event_value('-failure-', True)
	
		elif event == '-failure-':
			failure=values['-failure-']
			if failure==True:
				window['-multiline-'].update('One or more processes have failed. Unable to continue.'+'\n', append=True)
				progress_bar.update(bar_color=('red'))
			elif failure==False:
				window['-multiline-'].update('Conversion and bagging process is complete.'+'\n', append=True)
				progress_bar.UpdateBar(3,3)

		elif event == '-reset-':
			progress_bar.update(visible=False)
			window['-multiline-'].update('')
			window.find_element('-video-').update('')
			window.find_element('-filename-').update('')
		
		elif event == sg.WIN_CLOSED or event == 'Cancel':
			break
			window.close()

if __name__=='__main__':
	the_gui()

