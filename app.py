import click

@click.group()
def cli():
    pass

@cli.command()
def web():
    pass

if __name__ == '__main__':
    cli()
