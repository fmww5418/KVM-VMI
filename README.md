# KVM_VMI
<a href='https://pytorch.org/'><img src='https://img.shields.io/badge/python-2.7-green.svg?style=flat-square'></a> 

透過 libvirt 作為虛擬機管理介面，
並在 QEMU 上開設虛擬機，結合 LibVMI 進行虛擬機內省，
即可部署一個基於 VMI 的蜜罐(Honeypot) 或是惡意程式的測試平台(Testbed)。

此環境請使用 `Python 2`執行。

## Requirements

- [libvirt](https://github.com/libvirt/libvirt) (`> 4.0.0`)
- [QEMU](https://github.com/qemu/qemu) (`< 2.8.0`)
- [LibVMI](https://github.com/libvmi/libvmi) (`> 0.13.0`)
- [python-libvmi](https://github.com/libvmi/python) (`> 3.4.0`)
- [volatility](https://github.com/volatilityfoundation/volatility) (`> 2.6.1`)
- [Buildroot](https://buildroot.org/downloads/) (`= 2018.08.03`)
- [LiME](https://github.com/504ensicsLabs/LiME) 
- build-essential
- git 

## Note
- Libvirt 需自行編譯安裝 (LibVMI 需求)
> Ensure that your libvirt installation supports QMP commands,
 most prepackaged versions do not support this by default so you may need
 to install libvirt from source yourself
- Volatility 取證的 Linux kernel 版本不能太新，目前測試 4.9 以前的版本可以運行
> 32- and 64-bit Linux kernels from 2.6.11 to 4.2.3+ 

## Setup
- QEMU
```bash
$ sudo apt-get install qemu qemu-kvm
```
- Libvirt (version 4.0.0)
```bash
$ wget https://libvirt.org/sources/libvirt-4.0.0.tar.xz
$ tar Jxvf libvirt-4.0.0.tar.xz 
$ sudo apt-get install pkg-config libxml2-utils libxml2 libxml2-dev libyajl-dev xsltproc libdevmapper-dev libnl-3-dev libnl-route-3-dev libpciaccess-dev python-dev
$ cd libvirt-4.0.0
$ ./autogen.sh --system --enable-compile-warnings=error
$ make
$ sudo make install
```
- LibVMI
```bash
$ sudo apt-get install cmake flex bison libglib2.0-dev libvirt-dev libjson-c-dev libyajl-dev doxygen graphviz
$ git clone https://github.com/libvmi/libvmi
$ cd libvmi
$ mkdir build
$ cd build
$ cmake ..
$ make
$ sudo make install
$ ldconfig
```
-  LibVMI python
```bash
$ sudo apt-get install python3-pkgconfig python3-cffi python3-future python-setuptools python-pip
$ pip install -U setuptools wheel twine
$ git clone https://github.com/libvmi/python.git python-libvmi
$ cd python-libvmi
$ python setup.py build
$ sudo python setup.py install
```

- Volatility
```bash
$ git clone https://github.com/volatilityfoundation/volatility.git
$ sudo apt-get install yara python-pip dwarfdump
$ sudo -H pip install --upgrade pip
$ sudo -H pip install distorm3 pycrypto openpyxl Pillow
$ cd volatility
$ python setup.py build 
$ python setup.py install 
$ python vol.py --info    # test
```

- Buildroot
```bash
$ wget https://buildroot.org/downloads/buildroot-2018.08.3.tar.gz
$ tar xvf buildroot-2018.08.3.tar.gz
$ sudo apt-get install libncurses-dev build-essential 
$ sudo apt-get install texinfo unzip wget
$ sudo apt-get install libc6 libncurses5 libncurses5-dev libstdc++6
$ cd buildroot-2018.08.3
$ ls configs/
$ make qemu_x86_64_defconfig # select the config you wish to compile
$ make menuconfig            # select the packages you wish to compile
$ make busybox-menuconfig    # select the busybox setting you wish to compile
$ make -j`nproc`
```
- Python dependencies
```bash
$ python -m pip install --upgrade pip
$ pip install --user pyyaml pexpect
```

## Configure
需調整 config.ini 內的參數
- root        : 該專案在你作業系統內的絕對路徑
- lime_module:  編譯完 LiME 的 kernel module，需放在 guest VM 內，並更改在 VM 內對應的絕對路徑
- sysmap: guest VM OS system map 檔案，在 host 主機的絕對路徑
- LibVMI config 的設定請依照 LibVMI 的 linux_offset_tool 方法，更換這裡的設定為取得的對應值

## Troubleshooting
QEMU 2.11 以下的版本，在編譯時的錯誤 (make)
```bash
/home/qemu-m68k/util/memfd.c:40:12: error: static declaration of ‘memfd_create’ follows non-static declaration                                                                                                                      
 static int memfd_create(const char *name, unsigned int flags)                                                                                                                                                                                
            ^~~~~~~~~~~~                                                                                                                                                                                                                      
  CC      util/cacheinfo.o                                                                                                                                                                                                                    
In file included from /usr/include/x86_64-linux-gnu/bits/mman-linux.h:115:0,                                                                                                                                                                  
                 from /usr/include/x86_64-linux-gnu/bits/mman.h:45,                                                                                                                                                                           
                 from /usr/include/x86_64-linux-gnu/sys/mman.h:41,                                                                                                                                                                            
                 from /home/qemu-m68k/include/sysemu/os-posix.h:29,                                                                                                                                                                 
                 from /home/qemu-m68k/include/qemu/osdep.h:104,                                                                                                                                                                     
                 from /home/qemu-m68k/util/memfd.c:28:                                                                                                                                                                              
/usr/include/x86_64-linux-gnu/bits/mman-shared.h:46:5: note: previous declaration of ‘memfd_create’ was here                                                                                                                                  
 int memfd_create (const char *__name, unsigned int __flags) __THROW;                                                                                                                                                                         
     ^~~~~~~~~~~~                                                                                                                                                                                                                             
  CC      util/error.o                                                                                                                                                                                                                        
/home/qemu-m68k/rules.mak:66: recipe for target 'util/memfd.o' failed                                                                                                                                                               
make: *** [util/memfd.o] Error 1
```
Ans: `需補上修復的 patch`
```diff
diff --git a/configure b/configure
index 9c8aa5a..99ccc17 100755 (executable)
--- a/configure
+++ b/configure
@@ -3923,7 +3923,7 @@ fi
 # check if memfd is supported
 memfd=no
 cat > $TMPC << EOF
-#include <sys/memfd.h>
+#include <sys/mman.h>
 
 int main(void)
 {
diff --git a/util/memfd.c b/util/memfd.c
index 4571d1a..412e94a 100644 (file)
--- a/util/memfd.c
+++ b/util/memfd.c
@@ -31,9 +31,7 @@
 
 #include "qemu/memfd.h"
 
-#ifdef CONFIG_MEMFD
-#include <sys/memfd.h>
-#elif defined CONFIG_LINUX
+#if defined CONFIG_LINUX && !defined CONFIG_MEMFD
 #include <sys/syscall.h>
 #include <asm/unistd.h
```
 
Libvirt 的 default 網路沒有啟用
```bash
### virsh net-create 設定注意 (Persistent : no → yes) ###
$ virsh net-create default.xml  # create 後應該已經 start
$ virsh net-edit default        # 內容至少要有變化才會變 Persistent
$ virsh net-autostart default   # 啟動 autostart flag
```
```bash
$ virsh net-info default    # 查看預設網路的狀態
$ virsh net-dumpxml default # 查看預設網路的設定內容
$ virsh net-start default   # 預設網路是預設不開啟的，使用此指令開啟
```


LibVMI 執行 ./configure 的時候，出現 
>KVM Support  | --enable-kvm=no    | libvirt missing

Ans: `原因是預設 apt install 的 libvirt 不支援 QMP，需自行編譯安裝 libvirt`

LibVMI cmake 時，找不到 Xen store
> -- The C compiler identification is GNU 7.4.0
<br /> ... <br /> ...  <br />
Could NOT find Xenstore (missing: Xenstore_INCLUDE_DIR)
<br /> ... <br /> ...  <br />

Ans: `到 CMakefile.txt 將 Xen Enable option 改成 OFF`

LibVMI 執行 ./vmi-process-list 時，出現 Could not find a live guest VM or file to use.
> VMI_ERROR: Could not find a live guest VM or file to use.
<br/>VMI_ERROR: Opening a live guest VM requires root access.
Failed to init LibVMI library.
<br/>
*** 加上 debug flag 後的訊息 ***
<br /> --found KVM
<br /> ... <br /> ...  <br />
--Fail: incompatibility between libvmi and QEMU request definition detected
<br /> ... <br /> ...  <br />

Ans: `需使用 qemu 2.8 版本以下，詳細請見 libvmi/driver/kvm/kvm.c`
<br/>`但經過測試，將此判斷拿掉，使用 qemu 2.11 版的可以正常運行。`
```c
if (major >= 2 && minor >= 8) {
       dbprint(VMI_DEBUG_KVM, "--Fail: incompatibility between libvmi and QEMU request definition detected\n");
       goto out_error;
}
```

Volatility 執行 python vol.py –info 後出現錯誤
> Volatility Foundation Volatility Framework 2.6
<br/>*** Failed to import volatility.plugins.malware.apihooks (NameError: name 'distorm3' is not defined)
<br/>*** Failed to import volatility.plugins.malware.threads (NameError: name 'distorm3' is not defined)
<br/>*** Failed to import volatility.plugins.mac.apihooks_kernel (ImportError: No module named distorm3)
<br/>*** Failed to import volatility.plugins.mac.check_syscall_shadow (ImportError: No module named distorm3)
<br/>*** Failed to import volatility.plugins.ssdt (NameError: name 'distorm3' is not defined)
<br/>*** Failed to import volatility.plugins.mac.apihooks (ImportError: No module named distorm3)
<br/>ERROR   : volatility.debug    : You must specify something to do (try -h)

Ans: `安裝缺少的軟體包`
```bash
$ sudo apt-get install yara
$ sudo apt-get install python-pip
$ sudo -H pip install --upgrade pip
$ sudo -H pip install distorm3 pycrypto openpyxl Pillow
```

Volatility 執行 python vol.py –info 後出現錯誤 
> DEBUG   : volatility.debug    : Requested symbol do_fork not found in module kernel
<br/>No suitable address space mapping found
<br/>Tried to open image as:
<br/>MachOAddressSpace: mac: need base
<br/>LimeAddressSpace: lime: need base
<br/>WindowsHiberFileSpace32: No base Address Space
<br/> ... <br/> ...  <br/>
<br/> ArmAddressSpace: Failed valid Address Space check

Ans: `一是配置檔案沒有配置好，二是 kernel1 版本超過 4.9 版
在這裡是因為 Requested symbol do_fork not found in module kernel，版本過高的問題。`
