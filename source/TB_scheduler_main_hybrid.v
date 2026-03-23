//                ___   _   ___ _   ___
//               / __| /_\ | __/_\ / __|
//               \__ \/ _ \| _/ _ \\__ \
//               |___/_/ \_|_/_/ \_|___/
//
// Author:          Modified for Hybrid EDF+SRJF implementation
// Modified Date:   March 23, 2026
// Project Name:    SAFAS (Secure and Fast Hardware Scheduler)
// Target Device:   Virtex Family FPGA
// Tool versions:   Vivado 2018.2
//
// Licence:         These project have been published for academic use only under GPLv3 License.
//                  Copyright  2021-2026
//                  All Rights Reserved
//
// Description:     Testbench for Hybrid EDF+SRJF Scheduler
//                  Verifies the hybrid scheduling behavior with slack threshold
// 010100101000000100011010000001010011

`timescale 1ns / 1ns
module TB_scheduler_main_hybrid();

parameter W = 42;
parameter R_Q = 64;
parameter CORE = 16;

reg clk, rst;
reg wr;
reg [W-2:0] task_in;

wire CTRL_RP;
wire CTRL_subtract;
wire CTRL_MQ_active;
wire v_exch;
wire [W-2:0] task_exch;

// Instantiate the hybrid scheduler
Scheduler_main_hybrid #(.W(W), .R_Q(R_Q), .CORE(CORE)) UUT (
    .clk(clk),
    .rst(rst),
    .wr(wr),
    .task_in(task_in),
    .CTRL_RP(CTRL_RP),
    .CTRL_subtract(CTRL_subtract),
    .CTRL_MQ_active(CTRL_MQ_active),
    .v_exch(v_exch),
    .task_exch(task_exch)
);

// Clock generation
initial begin
    clk = 0;
    forever #5 clk = ~clk;
end

// Test stimulus
initial begin
    rst = 1;
    wr = 0;
    task_in = 0;

    #20 rst = 0;

    // Test Case 1: Task with high slack (should use SRJF)
    // Task: ID=1, Deadline=100, Execution=20, Slack=80 > 40 (2×20)
    #10;
    @(posedge clk);
    if(CTRL_MQ_active) begin
        wr = 1;
        task_in = {8'd1, 16'd100, 16'd20}; // ID=1, D=100, E=20
        @(posedge clk);
        wr = 0;
    end

    // Test Case 2: Task with low slack (should switch to EDF)
    // Task: ID=2, Deadline=30, Execution=20, Slack=10 < 40 (2×20)
    #100;
    @(posedge clk);
    if(CTRL_MQ_active) begin
        wr = 1;
        task_in = {8'd2, 16'd30, 16'd20}; // ID=2, D=30, E=20 - Low slack!
        @(posedge clk);
        wr = 0;
    end

    // Test Case 3: Multiple tasks with different slacks
    #100;
    @(posedge clk);
    if(CTRL_MQ_active) begin
        // Task with moderate slack
        wr = 1;
        task_in = {8'd3, 16'd50, 16'd15}; // ID=3, D=50, E=15, Slack=35 > 30
        @(posedge clk);
        wr = 0;
        #10;

        // Task with very low slack
        wr = 1;
        task_in = {8'd4, 16'd25, 16'd20}; // ID=4, D=25, E=20, Slack=5 < 40
        @(posedge clk);
        wr = 0;
        #10;

        // Short task (SRJF should prioritize)
        wr = 1;
        task_in = {8'd5, 16'd60, 16'd5}; // ID=5, D=60, E=5, Slack=55 > 10
        @(posedge clk);
        wr = 0;
    end

    // Run simulation
    #5000;

    // Display statistics
    $display("========================================");
    $display("Hybrid EDF+SRJF Scheduler Statistics");
    $display("========================================");
    $display("Total tasks received: %d", UUT.Scheduler.RP_RECEIVED);
    $display("Tasks scheduled via SRJF: %d", UUT.Scheduler.RP_SRJF_scheduled);
    $display("Tasks scheduled via EDF: %d", UUT.Scheduler.RP_EDF_scheduled);
    $display("Tasks preempted: %d", UUT.Scheduler.RP_preempted);
    $display("Tasks exchanged (overflow): %d", UUT.Scheduler.RP_Exchanged);
    $display("========================================");

    $finish;
end

// Monitor task scheduling
always @(posedge clk) begin
    if(wr && CTRL_MQ_active) begin
        $display("Time=%0t: Task submitted - ID=%d, Deadline=%d, Execution=%d, Slack=%d, Threshold=%d",
                 $time, task_in[39:32], task_in[31:16], task_in[15:0],
                 task_in[31:16] - task_in[15:0], task_in[15:0] << 1);
    end
end

endmodule
