import base64
import io
import nodes
import numpy as np
import safetensors
import socket
import torch
import zlib
from PIL import Image, ImageOps
from comfy.comfy_types.node_typing import IO
from comfy.utils import ProgressBar
from hashlib import sha256
from time import sleep

DEFAULT_ADDR = "127.0.0.1:8282"
MODE = ["Client", "Server"]

SEND_AS_PNG = "png"
SEND_AS_ZLIB = "zlib"
SEND_AS_RAW = "raw"
SEND_AS = [SEND_AS_PNG, SEND_AS_ZLIB, SEND_AS_RAW]


def ShowProgressBar(pbar, total, done, last_percent):
    current_percent = int((done / total) * 100) 
    if current_percent > last_percent:    
        pbar.update(current_percent - last_percent)
        last_percent = current_percent
    return last_percent


# tensors -> PNG images -> bytes
def ImgTensorsToBytes(tensors):
    bImages: List[bytes] = []

    # progress bar
    pbar = ProgressBar(100)
    total = len(tensors)
    done = 0
    last_percent = 0

    for (batch_number, image) in enumerate(tensors):
        i = 255. * image.cpu().numpy()
        img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
        buff = io.BytesIO()
        img.save(buff, "PNG")
        buff.seek(0)
        bImages.append(buff.read())

        # progress bar
        done += 1
        last_percent = ShowProgressBar(pbar, total, done, last_percent)

    allBuff = io.BytesIO()
    np.save(allBuff, bImages, allow_pickle=False)
    allBuff.seek(0)
    return allBuff.read()


# bytes -> PNG images -> tensors
def BytesToImgTensors(b):
    buff = io.BytesIO(b)
    bImages: List[bytes] = np.load(buff, mmap_mode=None, allow_pickle=False)
    tensors = []

    # progress bar
    pbar = ProgressBar(100)
    total = len(bImages)
    done = 0
    last_percent = 0

    for n in range( len(bImages) ):
        i = Image.open(io.BytesIO(bImages[n]))
        i = ImageOps.exif_transpose(i)
        if i.mode == 'I':
            i = i.point(lambda i: i * (1 / 255))
        image = i.convert("RGB")
        image = np.array(image).astype(np.float32) / 255.0
        image = torch.from_numpy(image)[None,]

        tensors.append(image)

        # progress bar
        done += 1
        last_percent = ShowProgressBar(pbar, total, done, last_percent)

    return torch.cat(tensors, dim=0)


# need to work on SSH Tunnel
def ConfirmConnection_Client(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while s.connect_ex((ip, port)) != 0:
        sleep(1)
    try:
        s.sendall(b"jumper_client")
        if s.recv(1024) == b"jumper_server":
            return s
    except:
        pass
    s.close()
    sleep(1)
    return False


def ConfirmConnection_Server(s):
    if s.recv(1024) == b'jumper_client':
        s.sendall(b'jumper_server')
        sleep(0.5)
    else:
        raise Exception('Receive unexpected data.')


def SendData(mode, addr, fileFormat, data):
    ip = addr.split(':')[0]
    port = int(addr.split(':')[1])

    h = sha256(data).hexdigest()
    data = base64.b64encode(data)
    data = fileFormat.encode('utf-8') + b'|' + h.encode('utf-8') + b'|' + data

    # add data size to be able to show progress bar on receive node
    data = str(len(data)).encode("utf-8") + b'|' + data

    if mode == "Client":

        # need to work on SSH Tunnel
        while True:
            s = ConfirmConnection_Client(ip, port)
            if s != False:
                break

        tosend = io.BytesIO(data)

        # progress bar
        pbar = ProgressBar(100)
        total = tosend.getbuffer().nbytes
        done = 0
        last_percent = 0

        while True:
            d = tosend.read(4096)
            if not d:
                break
            s.sendall(d)

            # progress bar
            done += len(d)
            last_percent = ShowProgressBar(pbar, total, done, last_percent)
            
        s.close()
        sleep(0.5)

    elif mode == "Server":
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((ip, port))
        server_socket.listen(1)

        s, addr = server_socket.accept()

        # need to work on SSH Tunnel
        ConfirmConnection_Server(s)

        tosend = io.BytesIO(data)

        # progress bar
        pbar = ProgressBar(100)
        total = tosend.getbuffer().nbytes
        done = 0
        last_percent = 0

        while True:
            d = tosend.read(4096)
            if not d:
                break
            s.sendall(d)

            # progress bar
            done += len(d)
            last_percent = ShowProgressBar(pbar, total, done, last_percent)

        s.close()
        sleep(0.5)

    else:
        raise Exception('mode is strange.')

    return


def RecvData(mode, addr, expect):
    ip = addr.split(':')[0]
    port = int(addr.split(':')[1])

    if mode == "Client":

        # need to work on SSH Tunnel
        while True:
            s = ConfirmConnection_Client(ip, port)
            if s != False:
                break

        torecv = io.BytesIO()

        # first data contain file size
        d = s.recv(4096)
        fileSize, d  = d.split(b'|', 1)
        torecv.write(d)

        # progress bar
        pbar = ProgressBar(100)
        total = int(fileSize.decode('utf-8'))
        done = len(d)
        last_percent = 0
        last_percent = ShowProgressBar(pbar, total, done, last_percent)

        while True:
            d = s.recv(4096)
            if not d:
                break
            torecv.write(d)

            # progress bar
            done += len(d)
            last_percent = ShowProgressBar(pbar, total, done, last_percent)

        s.close()
        sleep(0.5)

    elif mode == "Server":
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((ip, port))
        server_socket.listen(1)

        s, addr = server_socket.accept()

        # need to work on SSH Tunnel
        ConfirmConnection_Server(s)

        torecv = io.BytesIO()

        # first data contain file size
        d = s.recv(4096)
        fileSize, d  = d.split(b'|', 1)
        torecv.write(d)

        # progress bar
        pbar = ProgressBar(100)
        total = int(fileSize.decode('utf-8'))
        done = len(d)
        last_percent = 0
        last_percent = ShowProgressBar(pbar, total, done, last_percent)

        while True:
            d = s.recv(4096)
            if not d:
                break
            torecv.write(d)

            # progress bar
            done += len(d)
            last_percent = ShowProgressBar(pbar, total, done, last_percent)

        s.close()
        sleep(0.5)

    else:
        raise Exception('mode is strange.')

    torecv.seek(0)
    fileFormat, h, data = torecv.read().split(b'|', 2)
    fileFormat = fileFormat.decode('utf-8')
    h = h.decode('utf-8')
    data = base64.b64decode(data)

    # Hash check
    if ( h != sha256(data).hexdigest() ):
        raise Exception('Hash don\'t match.')

    # Returns
    if expect == "string":
        if fileFormat == "string":
            return data.decode('utf-8')
        else:
            raise Exception('Receive unexpected data.')
    elif expect == "images":
        if fileFormat == SEND_AS_PNG:
            return BytesToImgTensors(data)
        elif fileFormat == SEND_AS_ZLIB or fileFormat == SEND_AS_RAW:
            if fileFormat == SEND_AS_ZLIB:
                data = zlib.decompress(data)
            tensors = safetensors.torch.load(data)
            return tensors["jumper"]
        else:        
            raise Exception('Receive unexpected data.')
    
    return False


class SendString:
    @classmethod
    def IS_CHANGED(s, addr, mode, string, order):
        return float("NaN")

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
                    "addr": ("STRING", {"multiline": False, "default": DEFAULT_ADDR}),
                    "mode": (MODE, {"default": "Client"}),
                    "string": ("STRING", {"multiline": True, "default": ""}),
                },
                "optional": {
                    "order": ("INT", {"default": 0, "forceInput": True}),
                }
                }

    RETURN_NAMES = ("order",)
    RETURN_TYPES = ("INT",)
    FUNCTION = "f"
    CATEGORY = "Jumper"

    def f(self, addr, mode, string, order):
        SendData(mode, addr, "string", string.encode('utf-8'))
        return (order+1, )


class SendImages:
    @classmethod
    def IS_CHANGED(s, addr, mode, images, send_as, order):
        return float("NaN")

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
                    "addr": ("STRING", {"multiline": False, "default": DEFAULT_ADDR}),
                    "mode": (MODE, {"default": "Client"}),
                    "images": ("IMAGE", ),
                    "send_as": ( SEND_AS, {"default": SEND_AS_PNG}),
                },
                "optional": {
                    "order": ("INT", {"default": 0, "forceInput": True}),
                }
                }

    RETURN_NAMES = ("order",)
    RETURN_TYPES = ("INT",)
    FUNCTION = "f"
    CATEGORY = "Jumper"

    def f(self, addr, mode, images, send_as, order):
        if send_as == SEND_AS_PNG:
            data = ImgTensorsToBytes(images.contiguous())
        elif send_as == SEND_AS_ZLIB or send_as == SEND_AS_RAW:
            tensors = {"jumper": images.contiguous()}
            data = safetensors.torch.save(tensors)
            if send_as == SEND_AS_ZLIB:
                data = zlib.compress(data, 1)
        else:
            raise Exception('send_as is strange.')

        SendData(mode, addr, send_as, data)
        return (order+1, )


class ReceiveString:
    @classmethod
    def IS_CHANGED(s, addr, mode, order):
        return float("NaN")

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {       
                    "addr": ("STRING", {"multiline": False, "default": DEFAULT_ADDR}),
                    "mode": (MODE, {"default": "Client"}),
                    },
                "optional": {
                    "order": ("INT", {"default": 0, "forceInput": True}),
                }
                }

    RETURN_NAMES = ("string", "order")
    RETURN_TYPES = ("STRING",  "INT" )
    CATEGORY = "Jumper"
    FUNCTION = "f"

    def f(self, addr, mode, order):
        message = RecvData(mode, addr, "string")
        return (message, order+1) 


class ReceiveImages:
    @classmethod
    def IS_CHANGED(s, addr, mode, order):
        return float("NaN")

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {       
                    "addr": ("STRING", {"multiline": False, "default": DEFAULT_ADDR}),
                    "mode": (MODE, {"default": "Client"}),
                    },
                "optional": {
                    "order": ("INT", {"default": 0, "forceInput": True}),
                }
                }

    RETURN_NAMES = ("images", "order")
    RETURN_TYPES = ("IMAGE", "INT",)
    CATEGORY = "Jumper"
    FUNCTION = "f"

    def f(self, addr, mode, order):
        tensors = RecvData(mode, addr, "images")
        return (tensors, order+1)   


NODE_CLASS_MAPPINGS = {
    "Receive Images": ReceiveImages,
    "Receive String": ReceiveString,
    "Send Images": SendImages,
    "Send String": SendString,
}


NODE_DISPLAY_NAME_MAPPINGS = {
}
