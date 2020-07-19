---
layout: default
title:  "rgbctf2020 - Name a More Iconic Band - Writeup"
date:   2020-07-19 11:45:11 +0100
categories: rgbctf
---

## **Name a more iconic band**
Description: 
>I'll wait
>
>The flag for this challenge is all the passwords in alphabetical order, each separated by a single white-space as an MD5 hash in lower case


Category: *Beginner - Forensics*

First Blood: **1 hour, 24 minutes** after release  by team **redpwn**

Attempt this challenge with by downloading the [dump file][gdrive-memdump]

### **The Problem**
We are presented with a file with no extension and told we need to extract all of the passwords from it.

### **The Solution**
The first step is to identify what type of file this is. There are a few ways one might approach this.

How big is it?
{% highlight terminal %}
$ ls -hl
total 1.1G
-rw-r--r-- 1 klanec klanec 1.1G Jul  4 23:04 data
$ file data 
data: ELF 64-bit LSB core file, x86-64, version 1 (SYSV)
{% endhighlight %}

It seems to be an ELF file of around a gigabyte. That would be an odd size for an executable. Lets peak inside it a little bit. See the trimmed output below:

{% highlight terminal %}
$ strings data | head -n 25
VBCORE
VBCPU
...
Invalid partition table
Error loading operating system
Missing operating system
...
title Windows 7/Vista/Server
...
chainloader /bootmgr
title Windows 7/Vista/Server (No SLIC)
...
chainloader /bootmgr
{% endhighlight %}

I've trimmed out the irrelevant strings leaving the main tells that this is a dump of a virtual machine: `VBCORE`, `VBCPU`, references to `/bootmgr` combined with `Windows 7/Vista/Server`, virtual machine specific error strings near the top etc.

To confirm our suspicion, the first thing we should do is run `volatility imageinfo` against this. Volatility is a versatile tool for performing forensic analysis of memory dumps from a barrage of operating systems. the `imageinfo` module of volatility is the most basic analysis that we can perform that will (hopefully) return some basic information about the machine that this memory dump was harvested from. See below:

{% highlight terminal %}
$ volatility imageinfo -f data 
Volatility Foundation Volatility Framework 2.6
INFO    : volatility.debug    : Determining profile based on KDBG search...
          Suggested Profile(s) : Win7SP1x64, Win7SP0x64, Win2008R2SP0x64, Win2008R2SP1x64_24000, Win2008R2SP1x64_23418, Win2008R2SP1x64, Win7SP1x64_24000, Win7SP1x64_23418
                     AS Layer1 : WindowsAMD64PagedMemory (Kernel AS)
                     AS Layer2 : VirtualBoxCoreDumpElf64 (Unnamed AS)
                     AS Layer3 : FileAddressSpace (/home/klanec/Documents/CTF/rgbctf2020/radiohead/data)
                      PAE type : No PAE
                           DTB : 0x187000L
                          KDBG : 0xf8000183f110L
          Number of Processors : 1
     Image Type (Service Pack) : 1
                KPCR for CPU 0 : 0xfffff80001840d00L
             KUSER_SHARED_DATA : 0xfffff78000000000L
           Image date and time : 2020-07-04 03:41:04 UTC+0000
     Image local date and time : 2020-07-04 04:41:04 +0100
{% endhighlight %}

Great. This is a windows memory dump of the Windows 7 / Win 2008 Server era. This will enable us to potentially extract the NTLM hashes of the passwords from the dump. The next step is to use the `hivelist` module of volatility with one of the suggested profiles from above. `hivelist` lists the registry hives present in a particular memory image. 

>A hive is a logical group of keys, subkeys, and values in the registry that has a set of supporting files loaded into memory when the operating system is started or a user logs in.

Read more about that [here][hive-guide].

{% highlight terminal %}
$ volatility hivelist --profile Win7SP1x64 -f data 
Volatility Foundation Volatility Framework 2.6
Virtual            Physical           Name
------------------ ------------------ ----
0xfffff8a0000b1010 0x000000003bddd010 \SystemRoot\System32\Config\DEFAULT
0xfffff8a0001bd010 0x000000003b072010 \SystemRoot\System32\Config\SECURITY
0xfffff8a000935010 0x000000003cc02010 \Device\HarddiskVolume1\Boot\BCD
0xfffff8a000d97410 0x000000002ec00410 \SystemRoot\System32\Config\SOFTWARE
0xfffff8a00105c010 0x0000000034ae1010 \SystemRoot\System32\Config\SAM
0xfffff8a001113010 0x0000000034128010 \??\C:\Windows\ServiceProfiles\NetworkService\NTUSER.DAT
0xfffff8a001184010 0x000000003a916010 \??\C:\Windows\ServiceProfiles\LocalService\NTUSER.DAT
0xfffff8a001324010 0x000000002d801010 \??\C:\Users\in rainbows\ntuser.dat
0xfffff8a0014db010 0x000000002e2ee010 \??\C:\Users\in rainbows\AppData\Local\Microsoft\Windows\UsrClass.dat
0xfffff8a001b21010 0x000000001ad82010 \??\C:\Windows\System32\config\COMPONENTS
0xfffff8a001eee010 0x000000000734d010 \??\C:\Users\Administrator\ntuser.dat
0xfffff8a001ef9010 0x0000000005d52010 \??\C:\Users\Administrator\AppData\Local\Microsoft\Windows\UsrClass.dat
0xfffff8a006680010 0x000000001ce0d010 \??\C:\Users\ok computer\ntuser.dat
0xfffff8a006712010 0x000000000e3b1010 \??\C:\Users\ok computer\AppData\Local\Microsoft\Windows\UsrClass.dat
0xfffff8a00000e010 0x0000000001dea010 [no name]
0xfffff8a000023010 0x0000000001cb5010 \REGISTRY\MACHINE\SYSTEM
0xfffff8a00005d010 0x0000000001d71010 \REGISTRY\MACHINE\HARDWARE
{% endhighlight %}

We can take the `Virtual` offset of the `SAM` file and `SYSTEM` registry files located above and feed them into out the volatility `hashdump` module with the following syntax:

`volatility -f data --profile=$PROFILE hashdump -y $SYSTEM_OFFSET -s $SAM_OFFSET`

{% highlight terminal %}
$ volatility hashdump -f data --profile=Win7SP1x64 -y 0xfffff8a000023010 -s 0xfffff8a00105c010
Volatility Foundation Volatility Framework 2.6
Administrator:500:aad3b435b51404eeaad3b435b51404ee:756c599880f6a618881a49a9dc733627:::
Guest:501:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
pablo honey:1001:aad3b435b51404eeaad3b435b51404ee:7aaedbb86a165e8711cb46ee7ee2d475:::
the bends:1002:aad3b435b51404eeaad3b435b51404ee:dcbd05aa2cdd6d00b9afd4db537c4aa3:::
ok computer:1003:aad3b435b51404eeaad3b435b51404ee:74dea9ee338c5e0750e000d6e7df08e1:::
kid a:1004:aad3b435b51404eeaad3b435b51404ee:c9c55dd07a88b589774879255b982602:::
amnesiac:1005:aad3b435b51404eeaad3b435b51404ee:7b05eefac901e1c852baa61f86c4376f:::
hail to the thief:1006:aad3b435b51404eeaad3b435b51404ee:8eb2b699eeff088135befbde0880cfd4:::
in rainbows:1007:aad3b435b51404eeaad3b435b51404ee:419c1a5a5de0b529406fb04ad5e81d39:::
the king of limbs:1008:aad3b435b51404eeaad3b435b51404ee:a82da1c9a00f83a2ca303dc32daf1198:::
a moon shaped pool:1009:aad3b435b51404eeaad3b435b51404ee:4353a584830ede0e7d9e405ae0b11ea4:::
{% endhighlight %}

Wonderful. We were able to extract all the NTLM hashes from our memory dump. The above output is formatted as `USER:ID:LM hash:NTLM hash`, however the `aad3b435b51404eeaad3b435b51404ee` LM Hash simply means "no password". Read more about that [here][LMHASH].

Lets feed the NTLM hashes into [crackstation](https://crackstation.net/) and see what we can find:

{% highlight terminal %}
756c599880f6a618881a49a9dc733627	NTLM	supercollider
31d6cfe0d16ae931b73c59d7e0c089c0	NTLM	
7aaedbb86a165e8711cb46ee7ee2d475	NTLM	anyone can play guitar
dcbd05aa2cdd6d00b9afd4db537c4aa3	NTLM	my iron lung
74dea9ee338c5e0750e000d6e7df08e1	NTLM	karma police
c9c55dd07a88b589774879255b982602	NTLM	idioteque
7b05eefac901e1c852baa61f86c4376f	NTLM	pyramid song
8eb2b699eeff088135befbde0880cfd4	NTLM	there, there
419c1a5a5de0b529406fb04ad5e81d39	NTLM	weird fishes/arpeggi
a82da1c9a00f83a2ca303dc32daf1198	NTLM	lotus flower
4353a584830ede0e7d9e405ae0b11ea4	NTLM	burn the witch
{% endhighlight %}

So each user is a Radiohead album, and each password is a song from that album. Sorting the passwords alphabetically with a single whitespace delimiter and taking an MD5 hash of that reveals the flag:

`rgbCTF{cf271c074989f6073af976de00098fc4}`

[LMHASH]: https://www.yg.ht/blog/blog/archives/339/what-is-aad3b435b51404eeaad3b435b51404ee
[hive-guide]: https://docs.microsoft.com/en-us/windows/win32/sysinfo/registry-hives
[gdrive-memdump]: https://drive.google.com/uc?export=download&id=1rTbDMgL8CRIutqaX5T3y5YNLwYKqGbKp