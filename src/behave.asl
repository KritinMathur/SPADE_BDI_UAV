
+go_mission(positive) <-
    .mission(1, R);
    .reply(R);
    -go_mission(positive).

+rtl(positive) <-
    .rtl(1,R);
    .reply(R);
    -rtl(positive).

+fault_low_battery(positive) <-
    .fault_low_battery(1,R);
    .reply(R);
    -fault_low_battery(positive).

+fault_gps_lost(positive) <-
    .fault_gps_lost(1,R);
    .reply(R);
    -fault_gps_lost(positive).

+fault_near_neighbour(positive) <-
    .fault_near_neighbour(1,R);
    .reply(R);
    -fault_near_neighbour(positive).

