#!/usr/bin/env python3.5
from os import path
from re import search
from requests import get
from subprocess import Popen
from sys import argv,exit

### STEVENBLACK'S HOSTS FILE ###
# define url to Steven Black's hosts file.
stevenblack_hosts = "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts"

### FILES ###
# set the output filename to the same directory as this script.
output = path.join(path.dirname(__file__), "hosts.txt")

### FUNCTIONS ###
def remove_comment(line):
	# search for a comment within the current $line.
	m = search("#.*", line)
	# if no comments exist, then return the $line as is.
	if not m: return(line)
	# otherwise, define the comment's text.
	comment = m.group()
	# remove the comment and any extraneous whitespace.
	line = line.replace(comment, "").strip()
	# return the new line without its comment.
	return(line)

### DOWNLOAD ###
req_hosts = get(stevenblack_hosts)

if req_hosts.status_code == 200:
	hosts = req_hosts.text
else:
	print("STATUS CODE: %i" % (req_hosts.status_code))
	print("ERROR: Unable to download the hosts file at: '%s'" % (stevenblack_hosts))
	exit(1)

### REMOVE COMMENTS ###
# remove all comments.
hosts = [remove_comment(x) for x in hosts.split("\n") if not x.startswith("#")]

# remove empty entries.
hosts = [x for x in hosts if x]

### REMOVE EXTRANEOUS ###
# list of entries that are not needed in iOS.
blacklist = ["127.0.0.1 localhost", "127.0.0.1 localhost.localdomain", "127.0.0.1 local", "255.255.255.255 broadcasthost", "::1 localhost", "::1 ip6-localhost", "::1 ip6-loopback", "fe80::1%lo0 localhost", "ff00::0 ip6-localnet", "ff00::0 ip6-mcastprefix", "ff02::1 ip6-allnodes", "ff02::2 ip6-allrouters", "ff02::3 ip6-allhosts", "0.0.0.0 0.0.0.0"]

# remove all entries within the $blacklist from above and sort in alphabetical order.
hosts = sorted([x.strip() for x in hosts if x not in blacklist])

### FINISH ###
# join the list as a string.
hosts = "\n".join(hosts)

# write to output file.
with open(output, "w") as out: out.write("%s\n" % (hosts))
