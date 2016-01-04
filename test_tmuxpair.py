"""Collection of tests for tmuxpair.py"""
from distutils.version import LooseVersion
from textwrap import dedent
from copy import copy

from tmuxpair import main, __version__, AuthorizedKeys

import click
from click.testing import CliRunner
import sshkeys
import pytest
# standard fixtures: tmpdir


def test_authorized_keys(tmpdir):
    file_in = tmpdir.join("authorized_keys")
    authorized_keys_content = dedent(r'''
    command="/home/git/gitolite/src/gitolite-shell aXXXXXXXger",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDGfut9fyOSO2TTGM1DiqTQml2pULlxAet++yy0B2HdHismtZ8k71HrqhLt/AflOKQmEcyuYNtomKfV1K1wOtx7yBc2YsRiXhmPlH8QTL+a1KmDn7AEsFvN8vd9T27kqEPcVzRZqGgIOgKNu7ut8pP4Bl0gbbNgS+BNzjc0IQeieOmnOLmSWPwQ7Z/oR9FJvrsumNaAo4WnuOQa/R5EjkuAQbDbAUQvBmlXy9KtHo4izt0GUokenA2wS0PiEgRd2uj8dWWC3Uf3ZTnKo7jvXOBmPEAUOTA/65vwRNIc8K9XaekWzpItz1zsj9NQuKGCqLflCWzo1PpA5FUCI/xZsLgr andreas@XXXXXz
    command="/home/git/gitolite/src/gitolite-shell aXXXXXXXger",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDt+lvMRniCqRZxYvY2LqmYyUoD0K6RYFcPHNQSMn9d511dJVLhvtXFdn5kZCjSHVPaW2GWbX1CQYe8THFTu0wsKCv37c6S21jINljikoUwSXgl7vDJPgOZhLFYTEeSRVFNLkPJ/stNkBf847XbXT65Bf3t3VFhsnUuAsImJbANQEK9X2Xu3gMaeLOEsDHzAKr9/ZbDKisArAn7CoR2ZU3xt7MgcbywROoee9mPd9oI1ljYCOn8qOAFjyPigTVNlAiFYonISgxEAzBD18Nc35Yi+KfngLyCfsvfqmcCsSiSTywERetjJ/MtOjsdGN0nGspy3mWd8Ljfe3F7RSBQuXJl uk003019@rXXXvia
    command="/home/git/gitolite/src/gitolite-shell beXX",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDHF5ebpGGJLQFQsQnLX0qWJ7ehlH1OGMgMiY0FZiUXSpFjNZvVw/dn0hHHuO7HJIfa35KMgV8u+okVD6RUxlGdbRnJ3DFz+BrM7EdsRool9jIabjz65NaWdg0HDScQNpZneQn+HAd292Nq0UZSfP8lB1s8o8nwehvNLBqKJE9E/siblm/50rqEqXqhop96nPFBL5mVnYGhSYGxm4U3vNkIBR+x42Lsj2/LO1JGSZ7B2sDioZOlHHq3D4ep5ev2d/6rrzQkWJWt5CWWQzPuYcyvMc3yQehtqBKGAQUjbX6dG8nKuP7CnAweP62RO68/izHYTn9zLqsAQhwL3GLh+kTv uk0084XX@buXXXXim
    command="/home/git/gitolite/src/gitolite-shell beXX",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDLWsuwQnUxWW1ySWrb7t/k2Lrrr7px/QYIhNn0jxbfmba83bhCUTm+hczcLsH67SMqmYMhtZ2n+g1QZlEUQTr8q3N9fWcSMac9WL+Xks9x+umwmFuPMQq4kpPwugcLf1wGRZ2hDNi0zSh9Baw2BoS4Wx7fbngRG3CyxRQbdKKANn++HY+o/DL9hXcr8OQInaNxsRz7vLnhS3IxMsHmih0cvebhG1cyNNu0QIcV7ukThh7SUZDH+smB705jvAjfvYZH8Z1bPZjAXcekBe16heCbsGpi26MRVTYCzkaQuvnfQzkYpma8Ss7+G8GACu4cVuKU78a1oz6psmiXQqulvr+l uk0084XX@XXXXmon
    command="/home/git/gitolite/src/gitolite-shell beXX",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCu7n/7/CaucI/+PhF2rHvbwdny7Y75ddt9F/9fuXJlOM7hI5JUgZDajbeUO/+9bPzk/Vn1QfNfGJw/H00NMh2qGAFruu7ikHWDk2qBfYJH2pWIE5go0d226vu/PhcBYawaFd50wKG7fzCg4M4FG6SW+YwuzMonWU/IrYUECB34TgvW52AdC33T48eii289DAuq5k2T0pbZG4NhSip3XQxYOBp6vpQnFiX26PKvYC+UgB4ujj5527PD7WtCFFb2g1uhP0f7DHwE0GpevYdhnpeRwlEuJqnGmAlYvNW/NT5ECJ45GSKRXb6FHVG7IQ4ycD537ap+vC2bhR3wdTI6yxJt ben@loXXXXost
    command="/home/git/gitolite/src/gitolite-shell beXX",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDt/z1umZolo6OEnXzR+WzJYx4v5HufL+UkGt/Chb2RgwN4ntzxFaSMDITMd5VofZ/+dzqPTQIc3SlBW7WrOnwDsLkysarHzRJEyopVYJAaj5+tW9BQfeIn7H6fAQBCtve/w1W8pkK+Z4a8AIGv9UZ6eHPSPK5HYsYFaYVUikf9aCGhzgqYkQ6r+ekNWJw/m4LxIyA60avcanBHMS4oktCf2QgzbIlN8jNJ6Oz04GHPdqQ3xepba34pVOP4ICrVGVPfgabGihl4sJyA/Hw8UIaQranFeGI7IedNZdzvgGF8MgV7nHbZ7XDji2A+prFuX4juhZ1pzTTTdYnJFB2kE0xH Ben@BeXXXXc.local
    command="/home/git/gitolite/src/gitolite-shell beXX",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDzpU6DIuODjMkb2K3tDR3Nx1rv0OTT3+IzFyY3UXG3aZNVqzyepKOMSAd3K/u15tNUi4ajNUdEo1d4nVvt8g8RSKM3nCx/qApWvvvv/7kxMRKLMmdJB8CyfUws+WnlZQtpEbwq5w+aW2DQm04k4y4YCM6HJd/JTHmRB0MIG8adO5bLGsr8K75tXmVRkqZkGIr6soWS8H7N1o424UavqzdVf2Up1ZHmNJmw7Ly5Q59nf2oulDwFsPqp828t6kUa/jw+923v0jfT4aUt/AtHPwX8VEvkbZbeskTXAXpSmPthUjCwnKrhy1k5siez6bbfZQ6qODwdd3tValOmJdFt9f29 uk008XX7@XXXXiyot
    command="/home/git/gitolite/src/gitolite-shell ckXXXX",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDWcUKSLS8B7a9NyWDNFT9XJqC1vskT+DDRHHKCghTSBhyIfcUowwFm6rH0mCZXhT8bx4MLU7aE589cuWmI4tVII4Xq+NavKbsEamrpUpY4QGGX8843DNUsc7UhAYiCGW5IRX5JRlACB0rgqA8c9egMlnHc3n4Q45id1RuznM23U38nqyYEx6PHuVBnl5s8SrSgasMVb7zfYphINqx4nfW3qr8QDVsQ+4B6dfM5VadDTvg+wDHUNIp038aax56F2b4h0ArRybWarmT/OHXMBIYWXPq6DnQg+P4W8mOQ7HMSyJLSCXzaDzNjuL9O9zt3GcZ5SbMbcPEyDViekcGq9AkD uk003XXX@hXXXXem
    ''').strip()
    file_in.write(authorized_keys_content)
    ak1 = AuthorizedKeys.read(str(file_in))
    assert len(ak1) == 8
    assert str(ak1) == authorized_keys_content
    key = sshkeys.Key.from_pubkey_line(r'command="/home/git/gitolite/src/gitolite-shell beXX",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDzpU6DIuODjMkb2K3tDR3Nx1rv0OTT3+IzFyY3UXG3aZNVqzyepKOMSAd3K/u15tNUi4ajNUdEo1d4nVvt8g8RSKM3nCx/qApWvvvv/7kxMRKLMmdJB8CyfUws+WnlZQtpEbwq5w+aW2DQm04k4y4YCM6HJd/JTHmRB0MIG8adO5bLGsr8K75tXmVRkqZkGIr6soWS8H7N1o424UavqzdVf2Up1ZHmNJmw7Ly5Q59nf2oulDwFsPqp828t6kUa/jw+923v0jfT4aUt/AtHPwX8VEvkbZbeskTXAXpSmPthUjCwnKrhy1k5siez6bbfZQ6qODwdd3tValOmJdFt9f29 uk008XX7@XXXXiyot')
    assert key in ak1
    assert key.data in ak1
    file_out = tmpdir.join("authorized_keys.out")
    ak1.write(str(file_out))
    ak2 = AuthorizedKeys.read(str(file_out))
    for key in ak1:
        assert key in ak2
    key_file = tmpdir.join("key.pub")
    key_file_content = r'command="/home/git/gitolite/src/gitolite-shell beXX",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDE7TqUmphizXTvCOuRK2Xp0xFPHDGUL/2dduz00o4hZybdJsHNv5AqIvIeJWNbAZQX9kO0J8Offc2vk8aE0ab45hu2Csc4ektcjZ9uIsGslwHMrLXfTGi4PiTK9ddDYqNafIEtwvYW/89g+viHbIRZRcYkg0UeLvcTrm+pOCAjhGsVACs1s8m4e84zO+rvIeWVu6c4jrNy1XoOiElum68k60DXsiCYy6wo1eiIy0b4znU3i09wOnvINvLZ+STnXmmgizS2bNKw5wMxHbrKg9Y9lyuc0PX6ea2Mc5D1dupj1K57BXm8mYtBPgKsj+SPIoJKzMzmI6kq/6OJayk5XLp1 Ben@Ben-MXXXXr.local'
    key_file.write(key_file_content)
    key = sshkeys.Key.from_pubkey_file(str(key_file))
    assert key not in ak1
    ak1.add_key_file(str(key_file))
    assert (str(ak1)) == authorized_keys_content + "\n" + key_file_content
    assert key in ak1
    assert len(ak1) == 9
    ak1.extend(ak2)
    assert len(ak1) == 17
    ak2_copy = copy(ak2)
    assert ak2_copy is not ak2
    assert str(ak2_copy) == str(ak2)


def test_version():
    """Ensure that --version shows a version number that matches the
    __version__ defined in the module, and is parsable by LooseVersion"""
    runner = CliRunner()
    result = runner.invoke(main, args=['--version'])
    assert result.exit_code == 0
    version = result.output.split()[-1]
    assert version == __version__
    assert LooseVersion(version) >= LooseVersion('0.1.0')


def test_help():
    """Ensure that -h and --help display the help"""
    runner = CliRunner()
    result = runner.invoke(main, args=['-h'])
    result2 = runner.invoke(main, args=['--help'])
    assert result.exit_code == 0
    assert result.output.startswith("Usage:")
    assert result.output == result2.output
