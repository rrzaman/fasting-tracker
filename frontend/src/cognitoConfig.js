export const cognitoConfig = {
    authority: "https://cognito-idp.ca-west-1.amazonaws.com/ca-west-1_s938OjSzp",
    client_id: "77s4p5p4p8dr0gq1s1ubjq3f0j",
    redirect_uri: window.location.origin,
    response_type: "code",
    scope: "openid email profile",
    post_logout_redirect_uri: window.location.origin,
}