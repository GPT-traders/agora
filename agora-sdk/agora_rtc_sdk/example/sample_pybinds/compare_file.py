import filecmp


for i in range(10000):

    file_path1 = f'py_out_{i}.bin'
    file_path2 = f'../out/base_out_{i}.bin'
    print(filecmp.cmp('py_out_1000.bin', 'py_out_1500.bin', shallow=False))
    if not filecmp.cmp(file_path1, file_path2, shallow=False):
        print("The files are different.")
        print(file_path1,file_path2)
        break
