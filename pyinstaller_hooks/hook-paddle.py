# PyInstaller hook for paddlepaddle - 专门处理PaddlePaddle的复杂依赖
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_dynamic_libs
import os

# 收集PaddlePaddle的所有子模块
hiddenimports = []

try:
    print("Collecting all PaddlePaddle modules...")
    # 收集所有paddle子模块
    all_paddle_modules = collect_submodules('paddle')
    hiddenimports.extend(all_paddle_modules)
    print(f"Found {len(all_paddle_modules)} PaddlePaddle modules")
    
    # 特别确保关键模块被包含
    critical_paddle_modules = [
        'paddle',
        'paddle.base',  # 添加base模块
        'paddle.fluid',
        'paddle.fluid.core',
        'paddle.fluid.framework',
        'paddle.fluid.executor',
        'paddle.fluid.backward',
        'paddle.fluid.optimizer',
        'paddle.fluid.layers',
        'paddle.fluid.io',
        'paddle.fluid.dygraph',
        'paddle.fluid.dygraph.base',
        'paddle.fluid.dygraph.parallel',
        'paddle.fluid.contrib',
        'paddle.fluid.contrib.slim',
        'paddle.fluid.layers.tensor',
        'paddle.fluid.layers.math',
        'paddle.fluid.layers.nn',
        'paddle.fluid.layers.ops',
        'paddle.fluid.framework.io',
        'paddle.fluid.framework.variable',
        'paddle.fluid.framework.default_main_program',
        'paddle.fluid.framework.default_startup_program',
        'paddle.fluid.initializer',
        'paddle.fluid.clip',
        'paddle.fluid.param_attr',
        'paddle.fluid.learning_rate_scheduler',
        'paddle.fluid.transpiler',
        'paddle.fluid.incubate',
        'paddle.fluid.incubate.fleet',
        'paddle.fluid.incubate.fleet.base',
        'paddle.fluid.incubate.fleet.role_maker',
        'paddle.fluid.incubate.fleet.collective',
        'paddle.fluid.incubate.fleet.ps_dispatcher',
        'paddle.fluid.incubate.data_feeder',
        'paddle.fluid.incubate.tensor',
        'paddle.tensor',
        'paddle.nn',
        'paddle.nn.functional',
        'paddle.nn.layer',
        'paddle.nn.initializer',
        'paddle.nn.utils',
        'paddle.optimizer',
        'paddle.metric',
        'paddle.io',
        'paddle.vision',
        'paddle.vision.transforms',
        'paddle.vision.datasets',
        'paddle.vision.models',
        'paddle.text',
        'paddle.text.datasets',
        'paddle.audio',
        'paddle.audio.datasets',
        'paddle.incubate',
        'paddle.incubate.hapi',
        'paddle.incubate.distributions',
        'paddle.distribution',
        'paddle.distribution.normal',
        'paddle.distribution.uniform',
        'paddle.distribution.beta',
        'paddle.distribution.bernoulli',
        'paddle.jit',
        'paddle.jit.api',
        'paddle.jit.translated_layer',
        'paddle.jit.dy2static',
        'paddle.jit.dy2static.program_translator',
        'paddle.jit.dy2static.static_analysis',
        'paddle.jit.dy2static.utils',
        'paddle.autograd',
        'paddle.autograd.grad',
        'paddle.autograd.pybind',
        'paddle.device',
        'paddle.device.cuda',
        'paddle.device.cpu',
        'paddle.device.cuda.streams',
        'paddle.device.cuda.graph',
        'paddle.device.cuda.random',
        'paddle.device.cuda.nccl',
        'paddle.device.cuda.cub',
        'paddle.device.cuda.cudnn',
        'paddle.device.cuda.cufft',
        'paddle.device.cuda.curand',
        'paddle.device.cuda.cusolver',
        'paddle.device.cuda.cusparse',
        'paddle.device.cuda.cublas',
        'paddle.device.cuda.cudart',
        'paddle.device.cuda.common',
        'paddle.device.cuda.device',
        'paddle.device.cuda.stream',
        'paddle.device.cuda.event',
        'paddle.device.cuda.memory',
        'paddle.device.cuda.profiler',
        'paddle.device.cuda.random',
        'paddle.device.cuda.graph',
    ]
    
    for module in critical_paddle_modules:
        if module not in hiddenimports:
            hiddenimports.append(module)
            
except Exception as e:
    print(f"Warning: Could not collect all PaddlePaddle modules: {e}")
    # 回退到手动列表
    hiddenimports = [
        'paddle',
        'paddle.base',  # 添加base模块
        'paddle.fluid',
        'paddle.fluid.core',
        'paddle.fluid.framework',
        'paddle.fluid.executor',
        'paddle.fluid.backward',
        'paddle.fluid.optimizer',
        'paddle.fluid.layers',
        'paddle.fluid.io',
        'paddle.fluid.dygraph',
        'paddle.fluid.dygraph.base',
        'paddle.fluid.dygraph.parallel',
        'paddle.tensor',
        'paddle.nn',
        'paddle.nn.functional',
        'paddle.optimizer',
        'paddle.metric',
        'paddle.io',
        'paddle.jit',
        'paddle.autograd',
        'paddle.device',
    ]

# 收集数据文件
datas = []
try:
    paddle_data = collect_data_files('paddle')
    datas.extend(paddle_data)
    print(f"Found {len(paddle_data)} PaddlePaddle data files")
except Exception as e:
    print(f"Warning: Could not collect PaddlePaddle data files: {e}")

# 收集动态库
binaries = []
try:
    paddle_libs = collect_dynamic_libs('paddle')
    binaries.extend(paddle_libs)
    print(f"Found {len(paddle_libs)} PaddlePaddle dynamic libraries")
except Exception as e:
    print(f"Warning: Could not collect PaddlePaddle dynamic libraries: {e}")

# 不排除任何模块，但避免TensorRT相关警告
excludedimports = [
    'paddle.tensorrt',
    'paddle.inference.tensorrt', 
    'paddle.fluid.inference.tensorrt',
]

print(f"PaddlePaddle hook: Including {len(hiddenimports)} modules")
print(f"PaddlePaddle hook: Excluding {len(excludedimports)} problematic modules")