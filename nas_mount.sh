#sshfs -p 19840 -C -o idmap=user,allow_other mlevy@cs_srv_simu:/data /mnt/z
#mount --bind /mnt/z /mnt/nas_data

# To be run as sudo
ip li set mtu 1200 dev eth0  # change mtu in order to use ssh from WSL (don't know why...)
sshfs -p 22 -C -o idmap=user,allow_other mlevy@nas_corsicasole:/data /mnt/nas_data
