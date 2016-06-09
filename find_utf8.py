with open("update_schema.py", "r") as fp:
    for line in fp:
        line = line.strip()
        line=line.decode('utf-8','ignore').encode("utf-8")