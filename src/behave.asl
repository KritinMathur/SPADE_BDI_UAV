go_mission(positive).

+go_mission(positive) <-
    .mission(1, R);
    .reply(R);
    -go_mission(positive).

+rtl(positive) <-
    .rtl(1,R);
    .reply(R);
    -rtl(positive).