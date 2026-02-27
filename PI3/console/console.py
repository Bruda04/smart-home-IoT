def console_loop(registry, stop_event):
    while not stop_event.is_set():
        try:
            cmd = input("> ").strip().split()
            if not cmd:
                continue

            if cmd[0] == "list":
                print("Actuators:", ", ".join(registry.list()))

            elif cmd[0] == "on":
                if len(cmd) < 2:
                    print("Usage: on <actuator_name>")
                    continue
                act = registry.get(cmd[1].upper())
                if act:
                    act.on()
                else:
                    print(f"Actuator '{cmd[1]}' not found")

            elif cmd[0] == "off":
                if len(cmd) < 2:
                    print("Usage: off <actuator_name>")
                    continue
                act = registry.get(cmd[1].upper())
                if act:
                    act.off()
                else:
                    print(f"Actuator '{cmd[1]}' not found")

            elif cmd[0] == "display":
                if len(cmd) < 3:
                    print("Usage: display <actuator_name> <text>")
                    continue
                act = registry.get(cmd[1].upper())
                if act:
                    act.display(" ".join(cmd[2:]))
                else:
                    print(f"Actuator '{cmd[1]}' not found")

            elif cmd[0] == "clear":
                if len(cmd) < 2:
                    print("Usage: clear <actuator_name>")
                    continue
                act = registry.get(cmd[1].upper())
                if act:
                    act.clear()
                else:
                    print(f"Actuator '{cmd[1]}' not found")
                
            elif cmd[0] == "color":
                if len(cmd) < 3:
                    print("Usage: color <actuator_name> <r> <g> <b>")
                    continue
                act = registry.get(cmd[1].upper())
                if act:
                    try:
                        r, g, b = int(cmd[2]), int(cmd[3]), int(cmd[4])
                        act.set_color(r, g, b)
                    except ValueError:
                        print("Error: r, g, b must be integers")
                else:
                    print(f"Actuator '{cmd[1]}' not found")
            
            elif cmd[0] == "exit":
                print("Shutting down...")
                stop_event.set()
                break

        except EOFError:
            print("\nShutting down...")
            stop_event.set()
            break
        except Exception as e:
            print("Error:", e)

