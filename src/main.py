import plgnrtor
# import disease_facts
# import pest_facts
from plgnrtor import KBType

def main():
    # run prolog code gen.
    plgnrtor.run(KBType.LISTS)
    plgnrtor.run(KBType.NO_LISTS)

    # disease_facts.run()
    # pest_facts.run()


if __name__ == "__main__":
    main()
