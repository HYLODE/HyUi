vcl 4.1;

backend default {
    .host = "api";
    .port = "8000";
}
sub vcl_recv {
    /* other config here */

    if (req.http.X-Varnish-Nuke == "1") {
        set req.hash_always_miss = true;
    }
    if (req.method == "POST") {
    return (pass);
    }

    return(hash);
}
