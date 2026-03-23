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
// Description:     Hybrid Insertion Cell with Slack-based Priority
//                  - MODE = 0: SRJF - Compare by remaining execution time
//                  - MODE = 1: EDF - Compare by deadline (for tasks with low slack)
//                  - Slack = Relative_deadline - Execution_time
//                  - Low slack threshold = 2 × Execution_time
// 010100101000000100011010000001010011

`timescale 1ns / 1ns
module Insertion_cell_hybrid #(parameter W=41, MODE=0)(
   input clk, rst,
   input subtract,
   input wr,
   input rd,
   input[W-2:0] data_in,
   input[W-1:0] data_in_pre, // data from previous cell

   output reg[W-1:0] data_reg,
   output reg[W-2:0] data_out, // replacement with oldest data_reg or send data_in.
   output reg wr_pre
    );

wire[W-1:0] data_reg_sub;

// Slack calculation for incoming task
wire [15:0] slack_in = data_in[31:16] - data_in[15:0];  // deadline - execution
wire [15:0] threshold_in = data_in[15:0] << 1;          // 2 × execution time
wire low_slack_in = (slack_in < threshold_in);          // Is slack < 2×execution?

// Slack calculation for current cell task
wire [15:0] slack_reg = data_reg[31:16] - data_reg[15:0];
wire [15:0] threshold_reg = data_reg[15:0] << 1;
wire low_slack_reg = (slack_reg < threshold_reg);

// Comparison logic based on MODE and slack
wire comp;

generate
    if (MODE == 0) begin : SRJF_MODE
        // SRJF Mode: Compare by remaining execution time (shorter is higher priority)
        // But if a task has low slack, it should be moved to EDF queue (bit 40 = 1)
        assign comp = (data_reg[15:0] <= data_in[15:0]);
    end else begin : EDF_MODE
        // EDF Mode: Compare by deadline (earlier deadline is higher priority)
        // This queue handles tasks with low slack
        assign comp = (data_reg[31:16] <= data_in[31:16]);
    end
endgenerate

///////////////////////////////////////////////
// SUBTRACTOR
///////////////////////////////////////////////
sub_task_hybrid #(.W(W), .MODE(MODE)) subtractor(
    .clk  (clk),
    .rst  (rst),
    .subtract_en(subtract),
    .RT_in (data_reg),

    .RT_out(data_reg_sub)
);

///////////////////////////////////////////////
// Cell
///////////////////////////////////////////////
always @(posedge clk or posedge rst) begin
   if(rst) begin
      data_reg    <= {1'b0, {W-1{1'b1}}};
      data_out    <= {W-1{1'b1}};
      wr_pre      <= 1'b0;
   end else begin
      if (subtract)begin
           data_reg <= data_reg_sub; // subtract
      end else begin
   ///////////////////////////////////////////
   // write and read data from insertion sort
          case ({wr, rd})
            //normal
            2'b00 : data_reg   <= data_reg;
            //read
            2'b01 : data_reg   <= data_in_pre;
            //write
            2'b10 : data_reg   <=(comp & data_reg[W-1]) ? data_reg : {1'b1, data_in};
            //read_write
            2'b11 : data_reg   <= data_in_pre;
            endcase
        end
        // outputs
        wr_pre     <= (~rd)? (wr & data_reg[W-1]) : wr_pre;
        data_out   <= (~rd & wr)? ((comp & data_reg[W-1])? data_in : data_reg[W-2:0])
                                  : data_out;
   ///////////////////////////////////////////
   end
end
endmodule

///////////////////////////////////////////////
// Subtractor with Slack-aware priority switching
///////////////////////////////////////////////
module sub_task_hybrid #(parameter W=42, MODE=0)(
    input clk, rst,
    input subtract_en,
    input [(W)-1:0] RT_in,

    output reg[(W)-1:0] RT_out
   );

integer RP_MISS;
integer RP_SLACK_SWITCH;  // Count how many tasks switch to low-slack mode

wire check_miss = (RT_in[31:16] < RT_in[15:0]); //relative deadline < execution time

// Calculate slack after subtraction
wire [15:0] slack = RT_in[31:16] - RT_in[15:0];
wire [15:0] threshold = RT_in[15:0] << 1;  // 2 × execution time
wire low_slack = (slack < threshold) & (RT_in[31:16] != 0);

always @(posedge subtract_en, posedge rst) begin
  if(rst) begin
    RP_MISS = 0;
    RP_SLACK_SWITCH = 0;
  end else if(RT_in[W-1]) begin
    RT_out[15:0]  = RT_in[15:0];
    RT_out[31:16] = (RT_in[31:16]!=0)? RT_in[31:16] - 1 : RT_in[31:16]; //deadline
    RP_MISS = (check_miss)? RP_MISS+1:RP_MISS;

    // For SRJF queue (MODE=0), mark task as critical if slack is low
    // This will move it to the EDF queue in the next scheduling cycle
    if (MODE == 0 && low_slack && !RT_in[40]) begin
        RT_out[40] = 1'b1;  // Mark as critical/low-slack
        RP_SLACK_SWITCH = RP_SLACK_SWITCH + 1;
    end else begin
        RT_out[40] = RT_in[40];
    end

    RT_out[39:32] = RT_in[39:32];       // ID
    RT_out[W-1]   =(check_miss | RT_out[31:16]==0)? 1'b0:1'b1;
  end else RT_out = RT_in;
end

endmodule
