from ninja import Router

router = Router()


@router.get("/")
def get_auctions(request):
    return {"message": "Auctions API is working"}