import paddle
if paddle.is_compiled_with_cuda():
    print("CUDA GPU is available.")
else:
    print("CUDA GPU is not available.")