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

            elif cmd[0] == "start":
                if len(cmd) < 4 or cmd[1].upper() != "4SD":
                    print("Usage: start 4SD <minutes> <seconds>")
                    continue
                act = registry.get(cmd[1].upper())
                if act:
                    try:
                        minutes = int(cmd[2])
                        seconds = int(cmd[3])
                        act.set_time(minutes, seconds)
                    except ValueError:
                        print("Invalid minutes or seconds value")
                else:
                    print(f"Actuator '{cmd[1]}' not found")

            elif cmd[0] == "extend":
                if len(cmd) < 2 or cmd[1].upper() != "4SD":
                    print("Usage: extend 4SD")
                    continue
                act = registry.get(cmd[1].upper())
                if act:
                    act.add_seconds()
                else:
                    print(f"Actuator '{cmd[1]}' not found")

            elif cmd[0] == "set":
                if len(cmd) < 3 or cmd[1].upper() != "4SD":
                    print("Usage: set 4SD <seconds>")
                    continue
                act = registry.get(cmd[1].upper())
                if act:
                    try:
                        seconds = int(cmd[2])
                        act.set_add_seconds(seconds)
                    except ValueError:
                        print("Invalid seconds value")
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

