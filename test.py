a = 255
b = a.to_bytes(5,byteorder="big")
c = b[3:]
print(b[0:3],b,c,len(b))

