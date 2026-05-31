-- Forza Horizon 6 UDP telemetry dissector for Wireshark
-- Parses FH6 Data Out packets with the exact 324-byte layout.
--
-- Install by placing this file in your Wireshark plugins folder or loading it
-- via the Lua configuration file.
--
-- Default registration ports: 1050 and 20000. Adjust these as needed.

local proto = Proto("forzafh6", "Forza Horizon 6 Telemetry")

local f = proto.fields

f.is_race_on = ProtoField.int32("forzafh6.is_race_on", "Is Race On", base.DEC)

f.timestamp_ms = ProtoField.uint32("forzafh6.timestamp_ms", "Timestamp (ms)", base.DEC)

f.engine_max_rpm = ProtoField.float("forzafh6.engine_max_rpm", "Engine Max RPM")
f.engine_idle_rpm = ProtoField.float("forzafh6.engine_idle_rpm", "Engine Idle RPM")
f.engine_rpm = ProtoField.float("forzafh6.engine_rpm", "Current Engine RPM")

f.acceleration_x = ProtoField.float("forzafh6.acceleration_x", "Acceleration X")
f.acceleration_y = ProtoField.float("forzafh6.acceleration_y", "Acceleration Y")
f.acceleration_z = ProtoField.float("forzafh6.acceleration_z", "Acceleration Z")

f.velocity_x = ProtoField.float("forzafh6.velocity_x", "Velocity X")
f.velocity_y = ProtoField.float("forzafh6.velocity_y", "Velocity Y")
f.velocity_z = ProtoField.float("forzafh6.velocity_z", "Velocity Z")

f.angular_velocity_x = ProtoField.float("forzafh6.angular_velocity_x", "Angular Velocity X")
f.angular_velocity_y = ProtoField.float("forzafh6.angular_velocity_y", "Angular Velocity Y")
f.angular_velocity_z = ProtoField.float("forzafh6.angular_velocity_z", "Angular Velocity Z")

f.yaw = ProtoField.float("forzafh6.yaw", "Yaw")
f.pitch = ProtoField.float("forzafh6.pitch", "Pitch")
f.roll = ProtoField.float("forzafh6.roll", "Roll")

f.suspension_travel_fl = ProtoField.float("forzafh6.suspension_travel_fl", "Suspension Travel Front Left")
f.suspension_travel_fr = ProtoField.float("forzafh6.suspension_travel_fr", "Suspension Travel Front Right")
f.suspension_travel_rl = ProtoField.float("forzafh6.suspension_travel_rl", "Suspension Travel Rear Left")
f.suspension_travel_rr = ProtoField.float("forzafh6.suspension_travel_rr", "Suspension Travel Rear Right")

f.tire_slip_ratio_fl = ProtoField.float("forzafh6.tire_slip_ratio_fl", "Tire Slip Ratio Front Left")
f.tire_slip_ratio_fr = ProtoField.float("forzafh6.tire_slip_ratio_fr", "Tire Slip Ratio Front Right")
f.tire_slip_ratio_rl = ProtoField.float("forzafh6.tire_slip_ratio_rl", "Tire Slip Ratio Rear Left")
f.tire_slip_ratio_rr = ProtoField.float("forzafh6.tire_slip_ratio_rr", "Tire Slip Ratio Rear Right")

f.wheel_rotation_speed_fl = ProtoField.float("forzafh6.wheel_rotation_speed_fl", "Wheel Rotation Speed Front Left")
f.wheel_rotation_speed_fr = ProtoField.float("forzafh6.wheel_rotation_speed_fr", "Wheel Rotation Speed Front Right")
f.wheel_rotation_speed_rl = ProtoField.float("forzafh6.wheel_rotation_speed_rl", "Wheel Rotation Speed Rear Left")
f.wheel_rotation_speed_rr = ProtoField.float("forzafh6.wheel_rotation_speed_rr", "Wheel Rotation Speed Rear Right")

f.wheel_on_rumble_strip_fl = ProtoField.int32("forzafh6.wheel_on_rumble_strip_fl", "Wheel On Rumble Strip Front Left")
f.wheel_on_rumble_strip_fr = ProtoField.int32("forzafh6.wheel_on_rumble_strip_fr", "Wheel On Rumble Strip Front Right")
f.wheel_on_rumble_strip_rl = ProtoField.int32("forzafh6.wheel_on_rumble_strip_rl", "Wheel On Rumble Strip Rear Left")
f.wheel_on_rumble_strip_rr = ProtoField.int32("forzafh6.wheel_on_rumble_strip_rr", "Wheel On Rumble Strip Rear Right")

f.wheel_in_puddle_fl = ProtoField.int32("forzafh6.wheel_in_puddle_fl", "Wheel In Puddle Front Left")
f.wheel_in_puddle_fr = ProtoField.int32("forzafh6.wheel_in_puddle_fr", "Wheel In Puddle Front Right")
f.wheel_in_puddle_rl = ProtoField.int32("forzafh6.wheel_in_puddle_rl", "Wheel In Puddle Rear Left")
f.wheel_in_puddle_rr = ProtoField.int32("forzafh6.wheel_in_puddle_rr", "Wheel In Puddle Rear Right")

f.surface_rumble_fl = ProtoField.float("forzafh6.surface_rumble_fl", "Surface Rumble Front Left")
f.surface_rumble_fr = ProtoField.float("forzafh6.surface_rumble_fr", "Surface Rumble Front Right")
f.surface_rumble_rl = ProtoField.float("forzafh6.surface_rumble_rl", "Surface Rumble Rear Left")
f.surface_rumble_rr = ProtoField.float("forzafh6.surface_rumble_rr", "Surface Rumble Rear Right")

f.tire_slip_angle_fl = ProtoField.float("forzafh6.tire_slip_angle_fl", "Tire Slip Angle Front Left")
f.tire_slip_angle_fr = ProtoField.float("forzafh6.tire_slip_angle_fr", "Tire Slip Angle Front Right")
f.tire_slip_angle_rl = ProtoField.float("forzafh6.tire_slip_angle_rl", "Tire Slip Angle Rear Left")
f.tire_slip_angle_rr = ProtoField.float("forzafh6.tire_slip_angle_rr", "Tire Slip Angle Rear Right")

f.tire_combined_slip_fl = ProtoField.float("forzafh6.tire_combined_slip_fl", "Tire Combined Slip Front Left")
f.tire_combined_slip_fr = ProtoField.float("forzafh6.tire_combined_slip_fr", "Tire Combined Slip Front Right")
f.tire_combined_slip_rl = ProtoField.float("forzafh6.tire_combined_slip_rl", "Tire Combined Slip Rear Left")
f.tire_combined_slip_rr = ProtoField.float("forzafh6.tire_combined_slip_rr", "Tire Combined Slip Rear Right")

f.suspension_travel_meters_fl = ProtoField.float("forzafh6.suspension_travel_meters_fl", "Suspension Travel Meters Front Left")
f.suspension_travel_meters_fr = ProtoField.float("forzafh6.suspension_travel_meters_fr", "Suspension Travel Meters Front Right")
f.suspension_travel_meters_rl = ProtoField.float("forzafh6.suspension_travel_meters_rl", "Suspension Travel Meters Rear Left")
f.suspension_travel_meters_rr = ProtoField.float("forzafh6.suspension_travel_meters_rr", "Suspension Travel Meters Rear Right")

f.car_ordinal = ProtoField.int32("forzafh6.car_ordinal", "Car Ordinal")
f.car_class = ProtoField.int32("forzafh6.car_class", "Car Class")
f.car_performance_index = ProtoField.int32("forzafh6.car_performance_index", "Car Performance Index")
f.drivetrain_type = ProtoField.int32("forzafh6.drivetrain_type", "Drivetrain Type")
f.num_cylinders = ProtoField.int32("forzafh6.num_cylinders", "Number of Cylinders")
f.car_group = ProtoField.uint32("forzafh6.car_group", "Car Group")

f.smashable_vel_diff = ProtoField.float("forzafh6.smashable_vel_diff", "Smashable Velocity Difference")
f.smashable_mass = ProtoField.float("forzafh6.smashable_mass", "Smashable Mass")

f.position_x = ProtoField.float("forzafh6.position_x", "Position X")
f.position_y = ProtoField.float("forzafh6.position_y", "Position Y")
f.position_z = ProtoField.float("forzafh6.position_z", "Position Z")

f.speed_mps = ProtoField.float("forzafh6.speed_mps", "Speed (m/s)")
f.speed_kph = ProtoField.float("forzafh6.speed_kph", "Speed (km/h)")

f.power = ProtoField.float("forzafh6.power", "Power (W)")
f.torque = ProtoField.float("forzafh6.torque", "Torque (Nm)")

f.tire_temperature_fl = ProtoField.float("forzafh6.tire_temperature_fl", "Tire Temperature Front Left")
f.tire_temperature_fr = ProtoField.float("forzafh6.tire_temperature_fr", "Tire Temperature Front Right")
f.tire_temperature_rl = ProtoField.float("forzafh6.tire_temperature_rl", "Tire Temperature Rear Left")
f.tire_temperature_rr = ProtoField.float("forzafh6.tire_temperature_rr", "Tire Temperature Rear Right")

f.boost = ProtoField.float("forzafh6.boost", "Boost")
f.fuel = ProtoField.float("forzafh6.fuel", "Fuel")
f.distance_traveled = ProtoField.float("forzafh6.distance_traveled", "Distance Traveled")

f.best_lap = ProtoField.float("forzafh6.best_lap", "Best Lap")
f.last_lap = ProtoField.float("forzafh6.last_lap", "Last Lap")
f.current_lap = ProtoField.float("forzafh6.current_lap", "Current Lap")
f.current_race_time = ProtoField.float("forzafh6.current_race_time", "Current Race Time")

f.lap_number = ProtoField.uint16("forzafh6.lap_number", "Lap Number")
f.race_position = ProtoField.uint8("forzafh6.race_position", "Race Position")

f.accel_input = ProtoField.uint8("forzafh6.accel_input", "Accel Input")
f.brake_input = ProtoField.uint8("forzafh6.brake_input", "Brake Input")
f.clutch_input = ProtoField.uint8("forzafh6.clutch_input", "Clutch Input")
f.handbrake_input = ProtoField.uint8("forzafh6.handbrake_input", "Handbrake Input")
f.gear = ProtoField.uint8("forzafh6.gear", "Gear")

f.steer_input = ProtoField.int8("forzafh6.steer_input", "Steer Input")
f.steering = ProtoField.float("forzafh6.steering", "Steering")
f.normalized_driving_line = ProtoField.int8("forzafh6.normalized_driving_line", "Normalized Driving Line")
f.normalized_ai_brake_difference = ProtoField.int8("forzafh6.normalized_ai_brake_difference", "Normalized AI Brake Difference")

local function add_float_array(tree, tvb, base_offset, fields)
    for i = 1, #fields do
        tree:add_le(fields[i], tvb(base_offset + (i - 1) * 4, 4))
    end
end

local function add_int32_array(tree, tvb, base_offset, fields)
    for i = 1, #fields do
        tree:add_le(fields[i], tvb(base_offset + (i - 1) * 4, 4))
    end
end

function proto.dissector(tvb, pinfo, root)
    if tvb:len() ~= 324 then
        return
    end

    pinfo.cols.protocol = proto.name

    local subtree = root:add(proto, tvb(), "Forza Horizon 6 Telemetry")

    subtree:add_le(f.is_race_on, tvb(0, 4))
    subtree:add_le(f.timestamp_ms, tvb(4, 4))
    subtree:add_le(f.engine_max_rpm, tvb(8, 4))
    subtree:add_le(f.engine_idle_rpm, tvb(12, 4))
    subtree:add_le(f.engine_rpm, tvb(16, 4))

    subtree:add_le(f.acceleration_x, tvb(20, 4))
    subtree:add_le(f.acceleration_y, tvb(24, 4))
    subtree:add_le(f.acceleration_z, tvb(28, 4))

    subtree:add_le(f.velocity_x, tvb(32, 4))
    subtree:add_le(f.velocity_y, tvb(36, 4))
    subtree:add_le(f.velocity_z, tvb(40, 4))

    subtree:add_le(f.angular_velocity_x, tvb(44, 4))
    subtree:add_le(f.angular_velocity_y, tvb(48, 4))
    subtree:add_le(f.angular_velocity_z, tvb(52, 4))

    subtree:add_le(f.yaw, tvb(56, 4))
    subtree:add_le(f.pitch, tvb(60, 4))
    subtree:add_le(f.roll, tvb(64, 4))

    local susp_tree = subtree:add(proto, tvb(68, 16), "Suspension Travel")
    add_float_array(susp_tree, tvb, 68, {
        f.suspension_travel_fl,
        f.suspension_travel_fr,
        f.suspension_travel_rl,
        f.suspension_travel_rr,
    })

    local slip_ratio_tree = subtree:add(proto, tvb(84, 16), "Tire Slip Ratio")
    add_float_array(slip_ratio_tree, tvb, 84, {
        f.tire_slip_ratio_fl,
        f.tire_slip_ratio_fr,
        f.tire_slip_ratio_rl,
        f.tire_slip_ratio_rr,
    })

    local wheel_rot_tree = subtree:add(proto, tvb(100, 16), "Wheel Rotation Speed")
    add_float_array(wheel_rot_tree, tvb, 100, {
        f.wheel_rotation_speed_fl,
        f.wheel_rotation_speed_fr,
        f.wheel_rotation_speed_rl,
        f.wheel_rotation_speed_rr,
    })

    local rumble_tree = subtree:add(proto, tvb(116, 32), "Wheel Surface State")
    add_int32_array(rumble_tree, tvb, 116, {
        f.wheel_on_rumble_strip_fl,
        f.wheel_on_rumble_strip_fr,
        f.wheel_on_rumble_strip_rl,
        f.wheel_on_rumble_strip_rr,
    })
    add_int32_array(rumble_tree, tvb, 132, {
        f.wheel_in_puddle_fl,
        f.wheel_in_puddle_fr,
        f.wheel_in_puddle_rl,
        f.wheel_in_puddle_rr,
    })

    local surface_rumble_tree = subtree:add(proto, tvb(148, 16), "Surface Rumble")
    add_float_array(surface_rumble_tree, tvb, 148, {
        f.surface_rumble_fl,
        f.surface_rumble_fr,
        f.surface_rumble_rl,
        f.surface_rumble_rr,
    })

    local tire_slip_angle_tree = subtree:add(proto, tvb(164, 16), "Tire Slip Angle")
    add_float_array(tire_slip_angle_tree, tvb, 164, {
        f.tire_slip_angle_fl,
        f.tire_slip_angle_fr,
        f.tire_slip_angle_rl,
        f.tire_slip_angle_rr,
    })

    local tire_combined_slip_tree = subtree:add(proto, tvb(180, 16), "Tire Combined Slip")
    add_float_array(tire_combined_slip_tree, tvb, 180, {
        f.tire_combined_slip_fl,
        f.tire_combined_slip_fr,
        f.tire_combined_slip_rl,
        f.tire_combined_slip_rr,
    })

    local suspension_meters_tree = subtree:add(proto, tvb(196, 16), "Suspension Travel Meters")
    add_float_array(suspension_meters_tree, tvb, 196, {
        f.suspension_travel_meters_fl,
        f.suspension_travel_meters_fr,
        f.suspension_travel_meters_rl,
        f.suspension_travel_meters_rr,
    })

    subtree:add_le(f.car_ordinal, tvb(212, 4))
    subtree:add_le(f.car_class, tvb(216, 4))
    subtree:add_le(f.car_performance_index, tvb(220, 4))
    subtree:add_le(f.drivetrain_type, tvb(224, 4))
    subtree:add_le(f.num_cylinders, tvb(228, 4))
    subtree:add_le(f.car_group, tvb(232, 4))

    subtree:add_le(f.smashable_vel_diff, tvb(236, 4))
    subtree:add_le(f.smashable_mass, tvb(240, 4))

    subtree:add_le(f.position_x, tvb(244, 4))
    subtree:add_le(f.position_y, tvb(248, 4))
    subtree:add_le(f.position_z, tvb(252, 4))

    subtree:add_le(f.speed_mps, tvb(256, 4))
    local speed_mps = tvb(256, 4):le_float()
    subtree:add(f.speed_kph, speed_mps * 3.6)

    subtree:add_le(f.power, tvb(260, 4))
    subtree:add_le(f.torque, tvb(264, 4))

    local tire_temp_tree = subtree:add(proto, tvb(268, 16), "Tire Temperatures")
    add_float_array(tire_temp_tree, tvb, 268, {
        f.tire_temperature_fl,
        f.tire_temperature_fr,
        f.tire_temperature_rl,
        f.tire_temperature_rr,
    })

    subtree:add_le(f.boost, tvb(284, 4))
    subtree:add_le(f.fuel, tvb(288, 4))
    subtree:add_le(f.distance_traveled, tvb(292, 4))
    subtree:add_le(f.best_lap, tvb(296, 4))
    subtree:add_le(f.last_lap, tvb(300, 4))
    subtree:add_le(f.current_lap, tvb(304, 4))
    subtree:add_le(f.current_race_time, tvb(308, 4))

    subtree:add_le(f.lap_number, tvb(312, 2))
    subtree:add_le(f.race_position, tvb(314, 1))

    subtree:add_le(f.accel_input, tvb(315, 1))
    subtree:add_le(f.brake_input, tvb(316, 1))
    subtree:add_le(f.clutch_input, tvb(317, 1))
    subtree:add_le(f.handbrake_input, tvb(318, 1))
    subtree:add_le(f.gear, tvb(319, 1))

    subtree:add_le(f.steer_input, tvb(320, 1))
    local steer_value = tvb(320, 1):le_int()
    subtree:add(f.steering, steer_value / 127.0)

    subtree:add_le(f.normalized_driving_line, tvb(321, 1))
    subtree:add_le(f.normalized_ai_brake_difference, tvb(322, 1))
end

local udp_table = DissectorTable.get("udp.port")
udp_table:add(1050, proto)
udp_table:add(20000, proto)

-- Uncomment or add additional ports if your game is configured to send telemetry elsewhere.
-- udp_table:add(12345, proto)
