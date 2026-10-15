-- M0 input/evidence helper. Uses mGBA's public Lua API, never writes game RAM.
-- Load from mGBA Tools > Scripting after opening the locally compiled ROM.
local base = AVERON_EVIDENCE_DIR or 'C:/Users/kioco/OneDrive/Documents/ChatGPT/Pokemon Game/evidence/m0/'
local last = ''
local pending = nil
if AVERON_SMOKE_CB then callbacks:remove(AVERON_SMOKE_CB) end
local function log(message)
    local f = assert(io.open(base .. 'emulator-actions.log', 'a'))
    f:write(tostring(emu:currentFrame()) .. ' ' .. message .. '\n')
    f:close()
end
callbacks:add('crashed', function() log('CRASH') end)
callbacks:add('savedataUpdated', function() log('SAVE_DATA_UPDATED') end)
AVERON_SMOKE_CB = callbacks:add('frame', function()
    if pending then
        pending.left = pending.left - 1
        if pending.pulse and pending.left > pending.idle then
            emu:setKeys((pending.left % 30 < 2) and pending.mask or 0)
        end
        if pending.left == pending.idle then emu:setKeys(0) end
        if pending.left <= 0 then
            emu:setKeys(0)
            emu:screenshot(base .. pending.id .. '.png')
            log('DONE ' .. pending.id)
            pending = nil
        end
        return
    end
    local f = io.open(base .. 'input.txt', 'r')
    if not f then return end
    local command = f:read('*a')
    f:close()
    local id, mask, hold, idle = command:match('^(%w[%w_-]*) (%d+) (%d+) (%d+)')
    if not id or id == last then return end
    last = id
    mask, hold, idle = tonumber(mask), tonumber(hold), tonumber(idle)
    if hold > 3600 or idle > 3600 then return end
    log('INPUT ' .. command:gsub('\n', ' '))
    if id:match('^reset') then emu:reset() end
    local pulse = mask >= 1024
    if pulse then mask = mask - 1024 end
    emu:setKeys(mask)
    pending = {id=id, left=hold+idle, idle=idle, mask=mask, pulse=pulse}
end)
console:log('Averon M0 input and screenshot helper loaded')
