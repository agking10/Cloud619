# Cloud619
Code repository for final project for 601.619 Cloud Computing

To use this, first clone this directory into a mininet VM image at the root

In order to run this network, you need to have pox installed in the root directory. Additionally, you need to make this repository visible to pox. In the file ~/pox/pox/boot.py add the lines
	import sys
	sys.path.append("/root/Cloud619")
at the top of the file. If you are running this from our server, this has already been done. If you would like the key to the server please email agking10@gmail.com. Once you have the key you can ssh into the server by typing the following command into the terminal:

	ssh -i /path_to_key/TestServerkey.pem ubuntu@18.232.170.234

Next, type

	sudo su -
	cd Cloud619
	
======Running the controller========

To run a controller with ecmp load balancing, run the following command from the Cloud619 directory in a separate window:

	sudo sh start_ecmp.sh

You must start the controller before building the network.

=======Creating a fat tree network=======
In order to create a fat tree topology, run the following command:

	sudo sh create_network.sh

