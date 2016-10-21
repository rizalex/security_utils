import os

file_name = "/etc/selinux/config"
new_file_name = "/etc/selinux/config.new"
old_file_name = "/etc/selinux/config.old"

name_config = "SELINUX"
wrong_config1 = "disabled"
wrong_config2 = "permissive"
modify_config = "SELINUX=enforcing\n"


def chk_config(line):
    if name_config in line:
        if wrong_config1 in line.lower() or wrong_config2 in line.lower():
            return True

    return False

def make_configure():
    try:
        try:
            old_file = open(file_name, "r")
            new_file = open(new_file_name, "w")
            lines = old_file.readlines()
            for line in lines:
                    if chk_config(line):
                        new_file.write(modify_config)
                    else:
                        new_file.write(line)
        except Exception, e:
            print "[ERROR] make_configure", e
    finally:
        old_file.close()
        new_file.close()



if __name__ == "__main__":
    make_configure()
    print "[Success] file create: ", new_file_name
    os.rename(file_name, old_file_name)
    print "[Success] file copy: ", file_name, "->", old_file_name
    os.rename(new_file_name, file_name)
    print "[Success] file copy: ", new_file_name, "->", file_name


