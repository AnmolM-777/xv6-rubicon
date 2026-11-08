from bridge import XV6Bridge

bridge = XV6Bridge()

output = bridge.execute("ls")

print("Output from xv6:")
print(output)

bridge.close()
