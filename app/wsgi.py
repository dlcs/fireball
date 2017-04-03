from fireball import app as application
import logging

def setup_logging():
    """example docstring"""
    logging.basicConfig(filename="fireball.log",
                        filemode='a',
                        level=logging.DEBUG,
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s', )
    logging.getLogger('boto').setLevel(logging.ERROR)
    logging.getLogger('botocore').setLevel(logging.ERROR)
    logging.getLogger('werkzeug').setLevel(logging.DEBUG)

if __name__ == "__main__":
    setup_logging()
    application.run(debug=True)
