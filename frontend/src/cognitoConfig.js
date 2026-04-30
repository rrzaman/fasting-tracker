export const cognitoConfig = {
    authority: "https://cognito-idp.ca-west-1.amazonaws.com/ca-west-1_s938OjSzp",
    client_id: "n8fipk4bad7tgq93ivsu7q1ut",
    redirect_uri: window.location.origin,
    response_type: "code",
    scope: "openid email profile",
    post_logout_redirect_uri: window.location.origin,
}