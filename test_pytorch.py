import torch



def print_cuda():
    print(f"PyTorch版本: {torch.__version__}")
    print(f"CUDA可用: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA设备数量: {torch.cuda.device_count()}")
        print(f"当前设备: {torch.cuda.current_device()}")
        print(f"设备名称: {torch.cuda.get_device_name(0)}")
        
# async def test_gpu():
#     x = torch.rand(1000, 512).to("cuda")
#     y = self.semantic_model.encode([x])
#     print(f"运算设备: {y.device}")
    
print_cuda()