
+go_mission(positive) <-
    .mission(1, R);
    .reply(R);
    -go_mission(positive).

+hold_mission(positive) <-
    .pause(1, R);
    .reply(R);
    -hold_mission(positive).

+rtl(positive) <-
    .rtl(1,R);
    .reply(R);
    -rtl(positive).

+land(positive) <-
    .land(1, R);
    .reply(R);
    -land(positive).

+upload_mission(positive) <-
    .upload_mission(1,R);
    .reply(R);
    -upload_mission(positive).

+fault_low_battery(positive) <-
    .fault_low_battery(1,R);
    .reply(R);
    -fault_low_battery(positive).

+fault_gps_lost(positive) <-
    .fault_gps_lost(1,R);
    .reply(R);
    -fault_gps_lost(positive).

+fault_sensor_failure(positive) <-
    .fault_sensor_failure(1,R);
    .reply(R);
    -fault_sensor_failure(positive).

+fault_near_neighbour(positive) <-
    .fault_near_neighbour(1,R);
    .reply(R);
    -fault_near_neighbour(positive).

+fault_no_neighbour(positive) <-
    .fault_no_neighbour(1,R);
    .reply(R);
    -fault_no_neighbour(positive).
