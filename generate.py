#!/usr/bin/env python3.5
from collections import OrderedDict
from os import path
from re import search,sub,IGNORECASE
from requests import get
from subprocess import Popen
from sys import argv,exit

### PARAMETERS ###
# if the initial request to obtain the hosts list fails, then retry this many times.
max_retries = 10

### SOURCES ###
# dictionary containing the name and url for all files that will be used.
sources = OrderedDict()
# each source is contained on its own line for better readability.
sources["AD--disconnect"] = "https://s3.amazonaws.com/lists.disconnect.me/simple_ad.txt"
sources["AD--firebog_0"] = "https://v.firebog.net/hosts/AdguardDNS.txt"
sources["AD--firebog_1"] = "https://v.firebog.net/hosts/Easylist.txt"
sources["AD--firebog_2"] = "https://v.firebog.net/hosts/Prigent-Ads.txt"
sources["AD--squidblacklist"] = "https://www.squidblacklist.org/downloads/dg-ads.acl"
sources["HOSTS--stevenblack"] = "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts"
sources["MAL--disconnect"] = "https://s3.amazonaws.com/lists.disconnect.me/simple_malvertising.txt"
sources["MAL--firebog_0"] = "https://v.firebog.net/hosts/Prigent-Malware.txt"
sources["MAL--firebog_1"] = "https://v.firebog.net/hosts/Prigent-Phishing.txt"
sources["MAL--immortal_domains"] = "https://mirror.cedia.org.ec/malwaredomains/immortal_domains.txt"
sources["PRIV--firebog"] = "https://v.firebog.net/hosts/Easyprivacy.txt"
sources["PRIV--quidsup"] = "https://gitlab.com/quidsup/notrack-blocklists/raw/master/notrack-blocklist.txt"

### FILES ###
# set the output filename to the same directory as this script.
blacklist_txt = path.join(path.dirname(__file__), "blacklist.txt")

# custom list of domains to blacklist.
user_domains_txt = path.abspath(path.join(path.dirname(__file__), "user_domains.txt"))

### FUNCTIONS ###
def user_defined_domains():
	# display message to user.
	print("===> USER-DEFINED DOMAINS ('%s')" % (user_domains_txt))
	try:
		# read the user_domains.txt file and obtain all user-defined domains.
		with open(user_domains_txt, "r") as user_domains:
			contents = user_domains.readlines()
		# display message to user.
		print("SUCCESS")
	except FileNotFoundError:
		# display message to user.
		print("WARN: This file was not found, so no custom domains will be added.")
		# define an empty list.
		contents = []
	return(contents)

def download(name, url, contents, retry = 0):
	# display name of the current source.
	print("===> %s" % (name.upper()))
	# send a request to obtain the hosts list.
	req = get(url)
	# if the status code of this request was 200, then the request was successful.
	if req.status_code == 200:
		# add the contents for the current source ($name) to the $contents list. 
		contents.append(req.text)
		# display message to user.
		print("SUCCESS")
		# return the $contents list.
		return(contents)
	else:
		if retry == max_retry:
			# otherwise, display error messages to user.
			print("STATUS CODE: %i" % (req.status_code))
			print("FAIL: Unable to download the hosts file at: '%s'" % (url))
			# return here since there's nothing left to do.
			return
		else:
			print("INFO: Retry #%i" % (retry))
			# otherwise, retry the request again until the maximim number of retries has been reached.
			download(url, retry + 1)

def process(contents):
	# split each source's entries via newlines. This will create nested lists since the sources' entries are now being split.
	contents = [entry.split("\n") for entry in contents]
	# remove the comments from each individual entry if applicable. This formats the $contents list as one giant list again, no nested lists anymore.
	contents = [remove_comment(entry) for source in contents for entry in source]
	# remove the "0.0.0.0" ip address string from each entry if applicable.
	contents = [remove_ip(entry) for entry in contents]
	# remove the string "www." before each address since it is not needed.
	contents = [remove_www(entry) for entry in contents]
	# remove any invalid entries, such as those that don't start with a number or letter, or are '0.0.0.0' for instance.
	contents = [remove_invalid(entry) for entry in contents]
	# remove empty entries from the $contents list.
	contents = [entry.strip() for entry in contents if entry]
	# now remove all duplicates from the list and sort.
	contents = sorted(list(set(contents)))
	# return the list of $contents from all sources.
	return(contents)

def remove_comment(entry):
	# search for a comment within the current $entry, defined as starting with '#', and then remove it. If there are no comments, this will not affect anything.
	entry_no_comment = sub("#.*", "", entry).strip()
	# return the $entry.
	return(entry_no_comment)

def remove_ip(entry):
	# search for an ip address string in the entry by attempting to split via space. Then, only keep the website address, which will be the last entry. Eg. string "0.0.0.0 test.com" becomes ["0.0.0.0", "test.com"].
	address = entry.split(" ")[-1]
	# for good measure remove any extraneous spaces if possible and then return.
	return(address.strip())

def remove_www(entry):
	# search for 'www.' only in the start of the string. If it is found, then it is removed, otherwise the $entry is left as is.
	entry_no_www = sub("^www\.", "", entry, flags = IGNORECASE).strip()
	# return the $entry.
	return(entry_no_www)

def remove_invalid(entry):
	# if the entry is empty, immediately return.
	if not entry: return(None)
	# define the invalid starting characters of a web address as anything that is NOT a-z, A-Z, or 0-9.
	invalid = "^[^a-zA-Z0-9]"
	# define the format of an ip address.
	ip_address = "^[0-9]\.[0-9]\.[0-9]\.[0-9]$"
	# search for the invalid expressions defined above.
	x = search("(%s|%s)" % (invalid, ip_address), entry)
	# if the $entry matches any of these invalid expressions, then return None.
	if x:
		return(None)
	else:
		# otherwise, return the $entry as-is.
		return(entry)

def write(contents):
	# join the list into one string, newline delimited.
	contents = "\n".join(contents)
	# open the blacklist.txt file for writing.
	with open(blacklist_txt, "w") as blacklist:
		# write the contents to the output file.
		blacklist.write("%s\n" % (contents))

### MAIN ###
def main():
	# define the list that will hold all contents from all sources.
	contents = user_defined_domains()
	# iterate through each list and add its contents to the $contents list.
	for source in sources: contents = download(source, sources[source], contents)
	# obtain one list full of addresses from all sources.
	contents = process(contents)
	# write the addresses to the output file.
	write(contents)

### START ###
if __name__ == "__main__":
	main()
