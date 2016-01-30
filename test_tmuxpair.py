"""Collection of tests for tmuxpair.py"""
from distutils.version import LooseVersion
from textwrap import dedent
from copy import copy
from multiprocessing import Process
import subprocess
import shutil
import os
import time
import signal
import filecmp
import tmuxpair
from click.testing import CliRunner
import sshkeys
import pytest
# standard fixtures: tmpdir, monkeypatch, request


@pytest.fixture
def authorized_keys(tmpdir):
    """Return the filename of an authorized_keys file"""
    authorized_keys_file = tmpdir.join("authorized_keys")
    authorized_keys_content= dedent(r'''
    ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA6N/eQ1L0MxzzXgVpnnJCn6x+g+3434/ABLgG6IXbekYqBDWFOUfjslt90eTXRv5IVex1eY5RpR1d7dnFhYxW6bCZdrAryu9fPYSidFL3MGWTtijFRmSc9nCJVAP5+DY1xjA5aCtYq0MbhQMTRtBvOGPxFjXeG6sZ3dP698/am7KYjCUSqS2RBInEJ9J9Ym4lpCVptmnHWEJM8mc2PEa0PsuGBtxp2IaD7WO56ekaxy0+FlH2F93GsLDDqksxbcVp0UWoDW111CwFU3218z4TvjnftGoyLHMRDc6UmJallbpv/Ru+WeGCuCbzvzeoGVROxfBhLUji4idtMZlnWy3trQ== user@host
    ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA6clJaaa/7QtvyeTtD23AGEBau0BKePGtewVnoQjZ3UxAkJPUYslOIr4tyHbRZFB6mf8U2xUDgVSd99QwIJQIDpA5jHT6ro0lb9hhUGqqaqX0UKKm0s2w3LscuiSgUY+dfBQAhX48T8YNG2MLtx7fCHigV7lTUgJZci44QvcoHkUM9W89SmG1qb7Z4lFE/WFQWkymH+JPnwC4fkKYxBq5FcwoHvn2+Jf0uhHlxnrGbg+xJJjUFbCkL6OdH4XZjkK1Tg5FqS8vL6Wbl7NY7NG0MSDQrVzzDbDSmqvLc7vHnbkENJSg3p/pLTY5ILXL2SOVJOuvBqWgIVjU/AjX18UcYQ== user@host2
    ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA5dm/9BAeahUX5kQD90/2TMppY/mNoBHyie2RsKvAptjJBDtq4n9JQz0gKYKUAeeek5blrsoRTsobbDdjvZp4M4PJ1959sNvkyrNgqu9OtkxJRa8l+gpGBxq2bTJ5+UXHmYLCjCtVR+Ln/1BznV525LZac5s9hrtobJrLvFFAuvuIQXdetkJ2FKH+ZL8IJhDUNrPJznaYcHRlCxPfxZmfp6HBByWce5pN1s+p7NkqVFCjdusxr/a+SxeZr6f/yJGBGiIOnxc9tVl2bZ97MbwJ02ayCaTJCXRCtiAs+oKtD4Ev8wTXuLghvT2YiFV0focpRSgV0BMG3uzuklLLyjSLdQ== user@@host3
    ''').strip()
    authorized_keys_file.write(authorized_keys_content)
    return str(authorized_keys_file)

@pytest.fixture
def guest_key(tmpdir):
    guest_key_file = tmpdir.join("guest.pub")
    guest_key_content= dedent(r'''
    ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQ23sfV/f3dfAdfsPfs33edsfa039c3434/ABLgG6IXbekYqBDWFOUfjslt90eTXRv5IVex1eY5RpR1d7dnFhYxW6bCZdrAryu9fPYSidFL3MGWTtijFRmSc9nCJVAP5+DY1xjA5aCtYq0MbhQMTRtBvOGPxFjXeG6sZ3dP698/am7KYjCUSqS2RBInEJ9J9Ym4lpCVptmnHWEJM8mc2PEa0PsuGBtxp2IaD7WO56ekaxy0+FlH2F93GsLDDqksxbcVp0UWoDW111CwFU3218z4TvjnftGoyLHMRDc6UmJallbpv/Ru+WeGCuCbzvzeoGVROxfBhLUji4idtMZlnWy3trQ== guest@host
    ''').strip()
    guest_key_file.write(guest_key_content)
    return str(guest_key_file)


@pytest.fixture(params=[None, signal.SIGTERM])
def sig(request):
    return request.param


def test_tmuxpair(tmpdir, authorized_keys, guest_key, monkeypatch, sig):
    shutil.copy(authorized_keys, authorized_keys+".orig")
    check_output_log = os.path.join(str(tmpdir), "check_output.log")
    def mocked_check_output(*args, **kwargs):
        cmd = " ".join(args[0])
        with open(check_output_log, 'a') as log:
            log.write(cmd + "\n")
        if cmd == 'tmux attach -t pair':
            raise subprocess.CalledProcessError(returncode=1, cmd=cmd,
                                                output="No existing session")
        elif cmd == 'tmux new-session -s pair':
            if sig is None:
                time.sleep(2)
            else:
                time.sleep(60)
        elif cmd == 'tmux detach-client -s pair':
            pass
        else:
            raise ValueError("Unexpeced command: %s" % cmd)
    monkeypatch.setattr(subprocess, "check_output", mocked_check_output)

    runner = CliRunner()
    args = ['--debug', '--authorized_keys', authorized_keys, '--tmux', 'tmux', guest_key]
    p = Process(target=runner.invoke, args=(tmuxpair.main, ),
                kwargs={'args': args})
    p.start()
    # has the authorized_keys file been modified as expected?
    time.sleep(1)
    shutil.copy(authorized_keys, authorized_keys+".modified")
    with open(authorized_keys) as in_fh:
        authorized_keys_content = in_fh.read().strip()
        assert authorized_keys_content == dedent(r'''
        ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA6N/eQ1L0MxzzXgVpnnJCn6x+g+3434/ABLgG6IXbekYqBDWFOUfjslt90eTXRv5IVex1eY5RpR1d7dnFhYxW6bCZdrAryu9fPYSidFL3MGWTtijFRmSc9nCJVAP5+DY1xjA5aCtYq0MbhQMTRtBvOGPxFjXeG6sZ3dP698/am7KYjCUSqS2RBInEJ9J9Ym4lpCVptmnHWEJM8mc2PEa0PsuGBtxp2IaD7WO56ekaxy0+FlH2F93GsLDDqksxbcVp0UWoDW111CwFU3218z4TvjnftGoyLHMRDc6UmJallbpv/Ru+WeGCuCbzvzeoGVROxfBhLUji4idtMZlnWy3trQ== user@host
        ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA6clJaaa/7QtvyeTtD23AGEBau0BKePGtewVnoQjZ3UxAkJPUYslOIr4tyHbRZFB6mf8U2xUDgVSd99QwIJQIDpA5jHT6ro0lb9hhUGqqaqX0UKKm0s2w3LscuiSgUY+dfBQAhX48T8YNG2MLtx7fCHigV7lTUgJZci44QvcoHkUM9W89SmG1qb7Z4lFE/WFQWkymH+JPnwC4fkKYxBq5FcwoHvn2+Jf0uhHlxnrGbg+xJJjUFbCkL6OdH4XZjkK1Tg5FqS8vL6Wbl7NY7NG0MSDQrVzzDbDSmqvLc7vHnbkENJSg3p/pLTY5ILXL2SOVJOuvBqWgIVjU/AjX18UcYQ== user@host2
        ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA5dm/9BAeahUX5kQD90/2TMppY/mNoBHyie2RsKvAptjJBDtq4n9JQz0gKYKUAeeek5blrsoRTsobbDdjvZp4M4PJ1959sNvkyrNgqu9OtkxJRa8l+gpGBxq2bTJ5+UXHmYLCjCtVR+Ln/1BznV525LZac5s9hrtobJrLvFFAuvuIQXdetkJ2FKH+ZL8IJhDUNrPJznaYcHRlCxPfxZmfp6HBByWce5pN1s+p7NkqVFCjdusxr/a+SxeZr6f/yJGBGiIOnxc9tVl2bZ97MbwJ02ayCaTJCXRCtiAs+oKtD4Ev8wTXuLghvT2YiFV0focpRSgV0BMG3uzuklLLyjSLdQ== user@@host3
        command="tmux attach -t pair",no-port-forwarding ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQ23sfV/f3dfAdfsPfs33edsfa039c3434/ABLgG6IXbekYqBDWFOUfjslt90eTXRv5IVex1eY5RpR1d7dnFhYxW6bCZdrAryu9fPYSidFL3MGWTtijFRmSc9nCJVAP5+DY1xjA5aCtYq0MbhQMTRtBvOGPxFjXeG6sZ3dP698/am7KYjCUSqS2RBInEJ9J9Ym4lpCVptmnHWEJM8mc2PEa0PsuGBtxp2IaD7WO56ekaxy0+FlH2F93GsLDDqksxbcVp0UWoDW111CwFU3218z4TvjnftGoyLHMRDc6UmJallbpv/Ru+WeGCuCbzvzeoGVROxfBhLUji4idtMZlnWy3trQ== guest@host
        ''').strip()
    if sig is not None:
        pid = p.pid
        os.kill(pid, sig)
    p.join(60)
    # has the authorized_keys file been restored to the original?
    assert filecmp.cmp(authorized_keys, authorized_keys+".orig")

    # Did we make the expected calls to tmux?
    with open(check_output_log) as log:
        assert log.readlines() == [
        "tmux attach -t pair\n",
        "tmux new-session -s pair\n",
        "tmux detach-client -s pair\n" ]


def test_process_error(authorized_keys, guest_key, monkeypatch):
    def mocked_check_output(*args, **kwargs):
        cmd = " ".join(args[0])
        raise subprocess.CalledProcessError(returncode=1, cmd=cmd,
                                            output="test failure")
    monkeypatch.setattr(subprocess, "check_output", mocked_check_output)
    runner = CliRunner()
    args = ['--authorized_keys', authorized_keys, guest_key]
    result = runner.invoke(tmuxpair.main, args=args)
    assert "Cannot start tmux: test failure" in result.output
    assert result.exit_code == 1


def test_existing_backup(authorized_keys, guest_key, monkeypatch):
    shutil.copy(authorized_keys, authorized_keys+".tmuxpair_bak")
    runner = CliRunner()
    args = ['--authorized_keys', authorized_keys, guest_key]
    result = runner.invoke(tmuxpair.main, args=args)
    assert "already exists" in result.output
    assert result.exit_code == 1


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
    ak1 = tmuxpair.AuthorizedKeys.read(str(file_in))
    assert len(ak1) == 8
    assert str(ak1) == authorized_keys_content
    key = sshkeys.Key.from_pubkey_line(r'command="/home/git/gitolite/src/gitolite-shell beXX",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDzpU6DIuODjMkb2K3tDR3Nx1rv0OTT3+IzFyY3UXG3aZNVqzyepKOMSAd3K/u15tNUi4ajNUdEo1d4nVvt8g8RSKM3nCx/qApWvvvv/7kxMRKLMmdJB8CyfUws+WnlZQtpEbwq5w+aW2DQm04k4y4YCM6HJd/JTHmRB0MIG8adO5bLGsr8K75tXmVRkqZkGIr6soWS8H7N1o424UavqzdVf2Up1ZHmNJmw7Ly5Q59nf2oulDwFsPqp828t6kUa/jw+923v0jfT4aUt/AtHPwX8VEvkbZbeskTXAXpSmPthUjCwnKrhy1k5siez6bbfZQ6qODwdd3tValOmJdFt9f29 uk008XX7@XXXXiyot')
    assert key in ak1
    assert key.data in ak1
    file_out = tmpdir.join("authorized_keys.out")
    ak1.write(str(file_out))
    ak2 = tmuxpair.AuthorizedKeys.read(str(file_out))
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
    result = runner.invoke(tmuxpair.main, args=['--version'])
    assert result.exit_code == 0
    version = result.output.split()[-1]
    assert version == tmuxpair.__version__
    assert LooseVersion(version) >= LooseVersion('0.1.0')


def test_help():
    """Ensure that -h and --help display the help"""
    runner = CliRunner()
    result = runner.invoke(tmuxpair.main, args=['-h'])
    result2 = runner.invoke(tmuxpair.main, args=['--help'])
    assert result.exit_code == 0
    assert result.output.startswith("Usage:")
    assert result.output == result2.output
