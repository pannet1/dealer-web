from fastapi import FastAPI, HTTPException, Depends, Request


def verify_token(req: Request):
    token = req.headers["Authorization"]
    # Here your code for verifying the token or whatever you use
    if token is not valid:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True


@app.post("/auth")
async def login(password: str):
    if password == "my_password":
        return {"token": password}  # Generate your own token


@app.get("/")
async def home(authorized: bool = Depends(verify_token)):
    if authorized:
        return {"detail": "Welcome home"}


# to check if the request is coming from user or swagger
@app.post("/token")
async def login(req: Request, form_data: OAuth2PasswordRequestForm = Depends()):

    # Get header's data from the raw request
    # or from the swagger login form
    user = form_data.username
    print(user)
    print(req.headers["password"])

    return {"access_token": user, "token_type": "bearer"}
