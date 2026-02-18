import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import matplotlib.gridspec as gridspec
class Reporter:
    """
    Handles reporting and visualization of backtest results.
    """

    def __init__(self, all_results: dict[str, dict[str, float]]):
        """
        Initialize the Reporter with the list of trades.

        :param trades: List of trade dictionaries with entry/exit info and PnL.
        """
        self.results = all_results
        self.all_results = all_results
        self.current_sma = list(all_results.keys())[0]


    def print_summary(self):
        """
        Print a summary of backtest performance metrics.
        """
        print("Backtest Summary:")
        if len(self.results) == 0:
            print("No results to summarize.")
            return

        print("\n[⚠️ WARNING] Stocks with invalid stats (None or NaN):")
        for ticker, stats in self.results.items():
            if any(
                stats.get(k) is None or pd.isna(stats.get(k))
                for k in ['win_rate', 'avg_rr', 'avg_return']
            ):
                print(f" - {ticker}: {stats}")

        # סינון רק תוצאות תקינות
        valid_results = [
            r for r in self.results.values()
            if all(r.get(k) is not None and not pd.isna(r.get(k)) for k in ['win_rate', 'avg_rr', 'avg_return'])
        ]

        total_trades = sum(r.get('total_trades', 0) for r in valid_results)

        win_rate = sum(r['win_rate'] * r['total_trades'] for r in valid_results) / total_trades if total_trades > 0 else 0
        avg_rr = sum(r['avg_rr'] * r['total_trades'] for r in valid_results) / total_trades if total_trades > 0 else 0
        avg_return = sum(r['avg_return'] * r['total_trades'] for r in valid_results) / total_trades if total_trades > 0 else 0



        print(f"Total Trades: {total_trades}")
        print(f"Win Rate: {win_rate:.4f}")
        print(f"Average Risk-Reward Ratio: {avg_rr:.4f}")
        print(f"Average Return: {avg_return:.4f}")

    def plot_equity_curve(self):
        """
        Plot the equity curve of the backtest.
        """
        pass

    def _valid_results_df(self) -> pd.DataFrame:
        df = pd.DataFrame.from_dict(self.results, orient="index")
        df = df.dropna(subset=["win_rate", "avg_rr", "avg_return"])
        return df



    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt

    def plot_interactive_dashboard(self):
        """
        Presentation-grade trading dashboard.
        Fixes: Included all imports locally to prevent NameError.
        Features: Fade transitions, Break-even line, and Asset Tooltips.
        """
        # Essential Imports inside the function to prevent NameError
        from matplotlib.widgets import Button
        import matplotlib.gridspec as gridspec
        from matplotlib.ticker import ScalarFormatter

        plt.style.use("dark_background")

        sma_values = sorted(self.all_results.keys())
        if not sma_values:
            print("No results found.")
            return

        # --- UI Theme ---
        BG_COLOR = "#0b0614"
        ACCENT_PURPLE = "#bc13fe"
        INACTIVE_PURPLE = "#2d145c"
        TEXT_MAIN = "#ffffff"
        TEXT_DIM = "#cbb6ff"

        # --- Figure Architecture ---
        fig = plt.figure(figsize=(18, 11), facecolor=BG_COLOR)
        gs = gridspec.GridSpec(4, 1, height_ratios=[0.4, 0.4, 1.0, 5.0], hspace=0.25)

        nav_ax = fig.add_subplot(gs[0, 0])
        title_ax = fig.add_subplot(gs[1, 0])
        kpi_ax = fig.add_subplot(gs[2, 0])
        scatter_ax = fig.add_subplot(gs[3, 0])

        for ax in [nav_ax, title_ax, kpi_ax]:
            ax.axis("off")

        # Tracking state for interactivity
        state = {
            'active_sma': sma_values[0],
            'annot': None,
            'sc': None,
            'df': None
        }

        def get_data(sma):
            df = pd.DataFrame.from_dict(self.all_results[sma], orient="index")
            df['asset_name'] = df.index
            return df.dropna(subset=["win_rate", "avg_rr", "avg_return"])

        def update_ui_text(df, sma):
            title_ax.clear(); title_ax.axis("off")
            kpi_ax.clear(); kpi_ax.axis("off")

            title_ax.text(0.5, 0.5, f"Strategy Performance Landscape – SMA {sma}", 
                        fontsize=28, ha="center", va="center", color=TEXT_MAIN, weight='bold')

            if not df.empty:
                trades = int(df["total_trades"].sum())
                wr = np.average(df["win_rate"], weights=df["total_trades"])
                rr = np.average(df["avg_rr"], weights=df["total_trades"])

                # Large Display KPIs
                kpi_ax.text(0.15, 0.6, f"{trades:,}", fontsize=48, ha="center", weight='bold', color=TEXT_MAIN)
                kpi_ax.text(0.15, 0.1, "TOTAL TRADES", fontsize=14, ha="center", color=TEXT_DIM)

                kpi_ax.text(0.5, 0.6, f"{wr:.1%}", fontsize=48, ha="center", weight='bold', color=ACCENT_PURPLE)
                kpi_ax.text(0.5, 0.1, "AVG WIN RATE", fontsize=14, ha="center", color=TEXT_DIM)

                kpi_ax.text(0.85, 0.6, f"{rr:.2f}", fontsize=48, ha="center", weight='bold', color=TEXT_MAIN)
                kpi_ax.text(0.85, 0.1, "AVG RISK-REWARD", fontsize=14, ha="center", color=TEXT_DIM)

        def draw_plot(df, alpha=1.0):
            scatter_ax.clear()
            
            # 1. Break-even Curve: WinRate = 1 / (RR + 1)
            rr_range = np.logspace(np.log10(0.4), np.log10(max(df["avg_rr"]) * 1.5), 100)
            be_win_rate = 1 / (rr_range + 1)
            scatter_ax.plot(rr_range, be_win_rate, color=TEXT_MAIN, linestyle="--", alpha=0.3 * alpha)
            scatter_ax.fill_between(rr_range, be_win_rate, 1, color=ACCENT_PURPLE, alpha=0.03 * alpha)

            # 2. Plot Assets
            sizes = np.clip(df["total_trades"].to_numpy() * 0.6, 50, 800)
            state['sc'] = scatter_ax.scatter(
                df["avg_rr"], df["win_rate"],
                s=sizes, c=df["avg_return"],
                cmap="plasma", alpha=alpha, 
                edgecolors=TEXT_MAIN, linewidths=0.7
            )

            # 3. Clean X-Axis (Fixed NameError source)
            scatter_ax.set_xscale("log")
            scatter_ax.xaxis.set_major_formatter(ScalarFormatter())
            scatter_ax.set_xticks([0.5, 1, 2, 5, 10, 20, 50])
            
            scatter_ax.set_xlim(0.4, max(df["avg_rr"]) * 1.3)
            scatter_ax.set_ylim(0, 1.0)
            
            scatter_ax.grid(True, which="both", linestyle="--", alpha=0.1)
            scatter_ax.set_xlabel("Average Risk-Reward (Log Scale)", fontsize=14, color=TEXT_DIM)
            scatter_ax.set_ylabel("Win Rate (%)", fontsize=14, color=TEXT_DIM)

            # Tooltip initialization
            state['annot'] = scatter_ax.annotate("", xy=(0,0), xytext=(15,15),
                                                textcoords="offset points",
                                                bbox=dict(boxstyle="round", fc=BG_COLOR, ec=ACCENT_PURPLE, alpha=0.9),
                                                arrowprops=dict(arrowstyle="->", color=ACCENT_PURPLE))
            state['annot'].set_visible(False)

        # --- Interactivity Handlers ---
        def on_hover(event):
            if event.inaxes == scatter_ax:
                cont, ind = state['sc'].contains(event)
                if cont:
                    pos = state['sc'].get_offsets()[ind["ind"][0]]
                    state['annot'].xy = pos
                    asset = state['df'].iloc[ind["ind"][0]]['asset_name']
                    ret = state['df'].iloc[ind["ind"][0]]['avg_return']
                    state['annot'].set_text(f"{asset}\nReturn: {ret:+.1%}")
                    state['annot'].set_visible(True)
                    fig.canvas.draw_idle()
                else:
                    if state['annot'].get_visible():
                        state['annot'].set_visible(False)
                        fig.canvas.draw_idle()

        def transition(new_sma):
            if new_sma == state['active_sma']: return
            old_df = state['df']
            state['df'] = get_data(new_sma)

            # Faster transition for live presentation
            for a in np.linspace(1.0, 0.0, 5): 
                draw_plot(old_df, alpha=a)
                plt.pause(0.001)

            update_ui_text(state['df'], new_sma)

            for a in np.linspace(0.0, 1.0, 5):
                draw_plot(state['df'], alpha=a)
                plt.pause(0.001)
            
            state['active_sma'] = new_sma

        # --- Button Generation ---
        btns = {}
        for i, sma in enumerate(sma_values[:3]):
            ax_b = fig.add_axes([0.4 + i*0.09, 0.94, 0.08, 0.035])
            b = Button(ax_b, f"SMA {sma}", color=INACTIVE_PURPLE, hovercolor=ACCENT_PURPLE)
            b.label.set_color(TEXT_DIM); b.label.set_weight('bold')
            b.on_clicked(lambda e, v=sma: transition(v))
            btns[sma] = b

        # Initial Render
        state['df'] = get_data(state['active_sma'])
        update_ui_text(state['df'], state['active_sma'])
        draw_plot(state['df'])
        fig.canvas.mpl_connect("motion_notify_event", on_hover)

        plt.show()