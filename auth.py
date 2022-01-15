from boxsdk import OAuth2, Client

auth = OAuth2(
    client_id="uk7qibnrff37zjirky6jlmzdcjfoi6ar",
    client_secret="LoZJWONHEBxWTibrBkbQaOIa9Zvz5sNP",
)

auth_url, csrf_token = auth.get_authorization_url("http://127.0.0.1:5000/oauth2")
