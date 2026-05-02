import typer
import auth
import sys

app = typer.Typer(no_args_is_help=True)

@app.command()
def login():
    """Authenticate the CLI with Github"""
    typer.echo("starting the CLI with Github...")
    auth.login_flow()

@app.command()
def status():
    """check if  the user is currently logged in"""
    typer.check("status check coming soon")

def cli():
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "login":
            from auth import login_flow
            login_flow()
        elif command == "whoami":
            from auth import whoami
            whoami()
        else:
            print(f"unknown command {command}")
    else:
        print("Usage: insighta command")

if __name__ == "__main__":
    cli()
