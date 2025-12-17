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
                act = registry.get(cmd[1])
                if act:
                    act.on()
                else:
                    print(f"Actuator '{cmd[1]}' not found")

            elif cmd[0] == "off":
                if len(cmd) < 2:
                    print("Usage: off <actuator_name>")
                    continue
                act = registry.get(cmd[1])
                if act:
                    act.off()
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

