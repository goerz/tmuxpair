# tmuxpair #

[![Build Status](https://travis-ci.org/goerz/tmuxpair.svg)](https://travis-ci.org/goerz/tmuxpair)

Command line script for setting up a temporary tmux session for pair
programming.

© 2016 by [Michael Goerz](http://michaelgoerz.net). This software is available
under the terms of the [MIT license][LICENSE].

[LICENSE]: LICENSE

## Installation & Usage ##

Using [virtualenv][]/[pipsi][]/[conda env][] is recommended. Install the
`tmuxpair` executable with

    pip install tmuxpair

[virtualenv]: http://docs.python-guide.org/en/latest/dev/virtualenvs/
[pipsi]: https://github.com/mitsuhiko/pipsi#pipsi
[conda env]: http://conda.pydata.org/docs/using/envs.html

Run `tmuxpair -h` for usage details.

## Reasonably Secure Pair Programming ##

[A simple yet powerful way][1] for pair programming is to have a partner connect
to a tmux session on your machine. However, this implies that you give them SSH
access, with the obvious security implications: Your partner now
has complete control over your user account. They could use `scp` to copy any of
your files, read your email, or [pull a prank on you][2] by messing with your
`.bashrc`.

While you should probably only engage in pair programming with people that you
place a certain minimum amount of trust in, it would be nice to eliminate at
least the obvious ways for your partner to do anything behind your back.
`tmuxpair` achieves this by using [key-based authentication][3] together with the
feature of SSH to [limit a key to a specific command][4]. This follows the
approach outlined in [Tres Trantham’s blog post][5]. Note that we also lock down
`scp` access and port forwarding (which could allow your partner to access any
firewalled server on your network).

We can go a little further in ensuring only supervised access by strictly
limiting your partner’s connection to the duration of the pair-programming
session.`tmuxpair` does this by by wrapping `tmux`; when you run e.g.

    tmuxpair partner_key.pub

the public key in the file `partner_key.pub` is *temporarily* appended to your
`~/.ssh/authorized_keys` file (with the appropriate options), and `tmuxpair`
attaches to a tmux session “pair”. As soon as the session ends – or you detach
from it! – your partner’s SSH connection is closed and the original
`authorized_keys` file is restored.

Of course, if your partner were sufficiently determined to break into your
system, they could still manage to do so. Our assumption here is that
*supervised* access is “reasonably secure” in most environments. If your partner
does not need write access, `tmuxpair` provides a view-only mode that should not
leave any security loopholes.

Security could be enhanced further by running the tmux session under a separate
and dedicated account instead of your normal user account. However, the purpose
of the `tmuxpair` script is to provide a robust solution that allows you to
quickly share a terminal with a colleague, *without* any further setup.


[1]: https://blog.pivotal.io/pivotal-labs/labs/how-we-use-tmux-for-remote-pair-programming
[2]: http://unix.stackexchange.com/questions/232/unix-linux-pranks
[3]: https://www.digitalocean.com/community/tutorials/how-to-configure-ssh-key-based-authentication-on-a-linux-server
[4]: https://en.m.wikibooks.org/wiki/OpenSSH/Client_Configuration_Files#.7E.2F.ssh.2Fauthorized_keys
[5]: http://collectiveidea.com/blog/archives/2014/02/18/a-simple-pair-programming-setup-with-ssh-and-tmux/
