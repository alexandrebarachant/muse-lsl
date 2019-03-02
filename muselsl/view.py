
def view(window=5, scale=100, refresh=0.2, figure="15x6", version=1, type="eeg") :

	import viewer_eeg_v2 as v2
	import viewer_eeg_v1 as v1
	window = 5

	# TODO propose others viewers according to the streaming type
	'''
	if type == "ppg" or type == "PPG" :
		import viewer_ppg_v2 as v2
		import viewer_ppg_v1 as v1
		window = 3

	elif type == "gyro" or type == "GYRO"  :
	    import viewer_gyro_v2 as v2
	    import viewer_gyro_v1 as v1
	    window = 3

	elif type == "acc"  or type == "ACC" :
	    import viewer_acc_v2 as v2
	    import viewer_acc_v1 as v1
	    window = 3

	elif type == "telemetry"  or type == "TELEMETRY" :
	    import viewer_telemetry_v2 as v2
	    import viewer_telemetry_v1 as v1
	    window = 2
	'''

	if version == 2 :
	    v2.view()
	else :
	    v1.view(window, scale, refresh, figure)
