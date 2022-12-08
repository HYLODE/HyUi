vcl 4.1;

backend default {
    .host = "api";
    .port = "8000";
}

acl purge {
    "localhost";
}

sub vcl_recv {
    /* other config here */
    if (req.http.X-Varnish-Nuke == "1" && client.ip ~ purge) {
        set req.hash_always_miss = true;
    }
    /* ... */
}
