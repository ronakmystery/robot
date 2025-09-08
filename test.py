from manual_control import run_flask
from btcontroller import start_bt
import multiprocessing

if __name__ == "__main__":
    p1 = multiprocessing.Process(target=run_flask)
    p2 = multiprocessing.Process(target=start_bt)

    p1.start()
    p2.start()

    p1.join()
    p2.join()
