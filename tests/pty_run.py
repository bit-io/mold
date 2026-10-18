import pty, os, sys, time, select, struct, fcntl, termios, re
def run(binary, keys, rows=30, cols=100, wait=0.4):
    pid, fd = pty.fork()
    if pid == 0:
        os.execv(binary, [binary])
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
    out = b""
    def drain(t):
        nonlocal out
        end = time.time()+t
        while time.time() < end:
            r,_,_ = select.select([fd],[],[],0.05)
            if r:
                try: d = os.read(fd, 65536)
                except OSError: return
                if not d: return
                out += d
    drain(wait)
    for k in keys:
        if isinstance(k, tuple) and k[0]=="resize":
            fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", k[1], k[2], 0, 0)); 
        else:
            os.write(fd, k)
        drain(wait)
    drain(0.3)
    try: os.waitpid(pid, os.WNOHANG)
    except: pass
    return out
def screen(out, rows, cols):
    # tiny VT emulator: cursor addressing, SGR ignored, printable chars
    grid=[[" "]*cols for _ in range(rows)]
    s=out.decode("utf8","replace"); i=0; x=y=0
    while i < len(s):
        c=s[i]
        if c=="\x1b" and i+1<len(s) and s[i+1]=="[":
            j=i+2
            while j<len(s) and not ("@"<=s[j]<="~"): j+=1
            p=s[i+2:j]; f=s[j] if j<len(s) else ""
            if f=="H":
                a=p.split(";"); y=int(a[0] or 1)-1 if a and a[0] else 0; x=int(a[1])-1 if len(a)>1 and a[1] else 0
            elif f=="J" and p=="2": grid=[[" "]*cols for _ in range(rows)]
            i=j+1; continue
        if c=="\x1b": i+=2; continue
        if c=="\r": x=0
        elif c=="\n": y+=1
        elif ord(c)>=32:
            if 0<=y<rows and 0<=x<cols:
                grid[y][x]=c
                import unicodedata
                w=2 if unicodedata.east_asian_width(c) in "WF" else 1
                if w==2 and x+1<cols: grid[y][x+1]=""
                x+=w
            else: x+=1
        i+=1
    return "\n".join("".join(r).rstrip() for r in grid)
if __name__=="__main__":
    b=sys.argv[1]
    out=run(b,[b"a",b"\x1b[A",b"\x1b",b"b",("resize",20,60),b"x",b"q"])
    print(screen(out,30,100)[:300])
    print("raw-has-alt:", b"\x1b[?1049h" in out, "left-alt:", b"\x1b[?1049l" in out)
    print(out[-120:])
