-- No window: this suite only exercises data and hooks, and a LOVE process
-- that opens one on a build server is just a stray window.
function love.conf(t)
  t.window = false
  t.modules.audio = false
  t.modules.sound = false
  t.modules.physics = false
  t.modules.joystick = false
  t.console = true   -- lovec.exe: this is where the results are printed
end
