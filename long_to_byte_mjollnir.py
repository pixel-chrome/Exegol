from Crypto.Util.number import long_to_bytes

username = long_to_bytes(128672430374905338731062386)
password = long_to_bytes(33643248411776211125062560554130339746417025421355137140099645078910060553582)

print("username =", username)
print("password =", password)

print("username =", username.decode())
print("password =", password.decode())
