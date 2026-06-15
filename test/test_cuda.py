from rich.console import Console
from rich.panel import Panel

console = Console(force_terminal=True)

def print_cuda():
    console.print()
    console.print(Panel(
        "[bold cyan]💻 ----- PyTorch CUDA 环境检测 ----- [/bold cyan]",
        border_style="cyan",
        width=52,
    ))
    console.print("  [bold cyan]⏳ 正在检测 CUDA，请稍候 ...[/bold cyan]")

    import torch
    
    version = f"[green]{torch.__version__}[/green]"
    console.print(f"  📦 PyTorch 版本  [dim]→[/dim]  {version}")

    cuda_available = torch.cuda.is_available()
    if cuda_available:
        device_count = torch.cuda.device_count()
        current_device = torch.cuda.current_device()
        device_name = torch.cuda.get_device_name(0)

    if cuda_available:
        console.print(f"  ⚡ CUDA 可用      [dim]→[/dim]  [green]✔ True[/green]")
        console.print(f"  🔢 设备数量       [dim]→[/dim]  [green]{device_count}[/green]")
        console.print(f"  🎯 当前设备       [dim]→[/dim]  [green]{current_device}[/green]")
        console.print(f"  🏷️  设备名称       [dim]→[/dim]  [green]{device_name}[/green]")
        console.print()
        console.print(Panel(
            "[bold green]🎉 所有检测通过！CUDA 加速已就绪。[/bold green]",
            border_style="green",
            width=52,
        ))
        console.print()
    else:
        console.print(f"  ⚡ CUDA 可用      [dim]→[/dim]  [red]✘ False[/red]")
        console.print()
        console.print(Panel(
            "[bold yellow]⚠️  警告：未检测到 CUDA，将使用 CPU 推理。[/bold yellow]",
            border_style="yellow",
            width=52,
        ))
        console.print()


if __name__ == "__main__":
    print_cuda()
