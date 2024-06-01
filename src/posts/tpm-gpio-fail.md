<!--GEN_META
GEN_TITLE=TPM GPIO fail: How bad OEM firmware ruins TPM security
GEN_DESCRIPTION=In this article I demonstrate a software only attack that allows an operating system to set the PCRs of a discrete TPM device to arbitrary values and unseal any secret that uses a PCR based sealing policy (such as disk encryption keys used by unattended unlock TPM FDE schemes).
GEN_KEYWORDS=tpm,reset,gpio,fde
GEN_AUTHOR=Mate Kukri
GEN_TIMESTAMP=2024-06-01 18:36
GEN_COPYRIGHT=Copyright (C) Mate Kukri, 2024
-->

## Introduction

In this article I demonstrate a software attack that allows an operating system
to set the PCRs of a discrete TPM device to arbitrary values and unseal any
secret that uses a PCR based sealing policy (such as disk encryption keys used by
unattended unlock TPM FDE schemes).

## Previous work

We've previously demonstrated a trivial hardware attack <a href="https://hacky.solutions/blog/2024/02/tpm-attack">here</a>, that attack allowed an attacker with physical access to achieve
a clean TPM state by booting any operating system, then briefly grounding the reset pin
of a discrete TPM device with a pair of tweezers while the system was running.

Afterwards the attacker controlled operating system will still be executing, but now with
a "clean" TPM, allowing the attacker to perform arbitrary extend operations and derive
any desired PCR values.

The attack described here will achieve the same aim, but without the need to physically
manipulate pins on the device.

## Software attack

On Intel platforms, discrete TPM devices are connected to the PCH (Platform Controller Hub)
via some bus such as LPC or eSPI. These buses have a reset pin (PLTRST#), controlling the reset
state of devices. Normally this reset pin is controlled by hardware, and is only activated
on system reset, meaning that as per the TPM specification the TPM device will only be cleared
upon system reset.

Many pins on the PCH package, including the pins used by the LPC and eSPI buses, are multi use,
meaning they are shared with multiple IP blocks (aka logical components of an integrated circuit).
Software can select which "function" each pin is assigned to.
Among these is the GPIO (General Purpose Input Output) block, which is used to give software direct
control over a pin's state.

An operating system can (ab)use this by re-assigning the pin used for PLTRST# to the GPIO block,
and then driving it's value low from software via the GPIO block for some amount of time then
setting it back high. Any devices connected to the bus will react to this identically to "real"
reset request driven by hardware during platform reset.

In case of a TPM device attached to the bus, the above operation will result in the values of
the PCRs of the device being set to a "clean" state.
This then allows the same software that did the GPIO write operation to derive any desired
PCR values similar to the hardware attack, but this time without any physical access to pins on the
mainbaord.

A simple demonstration of the PCR values being cleared via software can be seen here:

<iframe width="560" height="315" src="https://www.youtube.com/embed/ayDFTBeiqZA?si=Sq06T_6oxUky1wab" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

This can be used to attack TPM FDE schemes (such as BitLocker) in multiple ways, for example:

- an attacker with brief physical access to a device can plug in a USB stick, boot the device from
  it, then extract the disk encryption key and encrypted data without any access to device internals;
- on a dual boot device, any operating system (including malware running inside any operating system)
  can access the encryption key and encrypted secrets stored on disk by other operating systems.

## Mitigating the attack

Fortunately Intel PCHs include a facility that allows boot firmware to lock the configuration of
PCH pins.

Boot firmware can set this lock, and thus preventing any software executing after it, such as
bootloaders and operating system kernels from executing this attack.
Intel claims that their (NDA-only) BIOS writers guide includes guidance on when and how to set
the GPIO lock bits.

Unfortunately the author have not so far managed to locate a device "in the wild" that implements
the lock correctly. The author also has no information whether or not this mechanism is implemented
in proprietary firmware kits such as AMI Aptio or Insyde H2O.

It appears that an implementation of this lock mechanism exists in the open source firmware project coreboot.
Unfortunately the mechanism is broken in its current state on platforms older then Meteor Lake, and most mainboard configurations don't include the correct GPIO definitions, but it is proof that this mechanism was at
least thought of by someone at some point.

Mitigating this attack will require rolling out boot firmware updates to affected devices.

## Attacking BootGuard's measured mode

Intel BootGuard is a feature provided by Intel platforms that allow boot firmware to be verified
and/or measured by hardware before being handed control of the platform.
One mode of BootGuard is "measurement only", where hardware extends TPM's PCRs with the hash of
boot firmware prior to handing control to it, but otherwise allowing any boot firmware to execute.

When used in conjunction with discrete TPM devices, malicious boot firmware can perform
the attack to reset then forge the measurements that were done by BootGuard prior to boot
firmware execution.

For this attack variant, the boot firmware setting the lock bit is obviously not a valid mitigation.
It was suggested to Intel, that as a mitigation against this variant, some pre-boot firmware platform
component such as the Intel CSME could set the lock bit.

Intel rejected implementing any mitigation against this, arguing that they do not consider this variant a vulnerability in
BootGuard at all, in their words:

> As per architecture the Measured Boot mode attack is not a concern. We do have verified boot, in the sense that that the FW that can access the configuration is clearly in the TCB and it is absolutely verified (i.e. Intel authentic FW).

> On the other hand, the attack in question he have a concern with, starts by having physical access. In this particular case, I don’t think it is even relevant:

> If attacker have physical access, the discrete TPM is an attack surface anyway and even a known attack already. Attacker can use an interposer (just connect the TPM over a different crafted connector, very simple physical attack) and control whatever the TPM is storing regardless of FW intervention/compromise/reflashing. So the issue of the GPIO unlock is only applicable for SW only attack (no physical access).

This is right in a strict sense (and is even minimizing the problem, as the tweezer attack is
much easier to do then invasive attacks such the interposer attack).
For one time disk decryption, the tweezer attack is just as effective, and is arguably faster
to execute then overwriting the platform's flash.

However the author believes that there are scenarios where the GPIO reset attack can still pose problems beyond
existing issues. For instance in as evil housekeeper attack, the device owner would like to detect tampering with boot firmware after leaving the device unattended via verifying the TPM measurements.

Here, the GPIO reset attack can be used by simply overwriting the SPI flash, and then replacing the device.
After this any protection offered by BootGuard measurements would be lost, and the device owner would never know that
the device is running tampered firmware.
In comparison, an interposer attack would be rather invasive and hard to implement in a permanent manner in a device
that the attacker is wanting to return to the victim afterwards.

## Disclosure notes

This was first disclosed to Intel Product Security privately on the 27th February, 2024.

Intel claims that this vulnerability doesn't directly affect Intel products.
This claim is justified by the statement the NDA-only BIOS writer's guide supposedly
includes guidance for OEMs on how and when to set the GPIO lock bits.

Intel initially claimed that this is firmware vulnerability only affecting MSI products.

This was weird considering that the author never mentioned MSI to Intel.

After some back and forth, Intel said that this vulnerability may affect an
unspecified set of OEM partners, and also said they will to inform their
partners about it and reinforce their security.

A CVE wasn't assigned by Intel, and the author is unsure if Intel has actually
informed any other party.

A public disclosure date of 1st June was agreed on the 4th of April. This article is being
released in accordance with said disclosure date to bring attention to the issue,
and hopefully a start the process of rolling out mitigations for it.

## Testing your system

The author intends to implement support for detecting this vulnerability in the chipsec framework,
when done so, link will be included here.
