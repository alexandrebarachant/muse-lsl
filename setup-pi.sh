sudo apt-get update
sudo apt-get install -y python3-pip libatlas-base-dev git
sudo pip3 install muselsl
wget https://github.com/sirexeclp/muse-lsl/releases/download/1/liblsl32.so
sudo cp liblsl32.so /usr/local/lib/python3.7/dist-packages/pylsl/liblsl32.so
git clone https://github.com/sirexeclp/muse-lsl.git
cd muse-lsl && git checkout feature/experiment
