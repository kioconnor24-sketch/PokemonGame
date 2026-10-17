@ Standalone original homebrew, NOT an Averon cartridge/linker change.
@ No Nintendo logo/assets. mGBA runner skips BIOS; this is a mapping proof,
@ not hardware boot, graphical, sound, battle, save or Delta acceptance.
@ Assemble/link at 0x08000000; objcopy to a local binary; pad to 64 MiB.
@ Put words 0x11223344 at file 0x2000, 0x55667788 at 0x02000000,
@ and 0x99aabbcc at 0x03fff000. Matrix header begins with M at 0xac.
@ A second negative control replaces that M with B. Run with
@ mgba-rom-test -S 3 -R r0 file.gba: expected exits 0 and 1 respectively.
@ Re-map only page 0x1000; executing code/header stays in the first page.
    .syntax unified
    .cpu arm7tdmi
    .arm
    .global _start
_start:
    b start
    .space 0xa0 - (. - _start)
    .ascii "CAPACITYTEST"
    .ascii "MCXE"
    .ascii "00"
    .byte 0x96
    .space 0xc0 - (. - _start)
start:
    ldr r4, =0x08800100
    ldr r5, =0x08001000
    ldr r0, =0x02000000
    bl map_page
    ldr r1, [r5]
    ldr r2, =0x55667788
    cmp r1, r2
    bne failed
    ldr r0, =0x03fff000
    bl map_page
    ldr r1, [r5]
    ldr r2, =0x99aabbcc
    cmp r1, r2
    bne failed
    ldr r0, =0x00002000
    bl map_page
    ldr r1, [r5]
    ldr r2, =0x11223344
    cmp r1, r2
    bne failed
    mov r0, #0
    b done
failed:
    mov r0, #1
done:
    swi 0x030000
    b done
map_page:
    str r0, [r4, #4]
    mov r1, #0x1000
    str r1, [r4, #8]
    mov r1, #1
    str r1, [r4, #12] @ count of 512-byte pages
    str r1, [r4, #0]  @ remap command
    bx lr
    .ltorg
